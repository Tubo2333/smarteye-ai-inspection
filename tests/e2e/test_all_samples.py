"""
E2E 测试：对所有示例图片调用检测 API，验证无报错
"""
import base64
import os
import requests
import time

API = "http://127.0.0.1:8000"
SAMPLE_DIR = "data/sample_images"

def test_all_sample_images():
    """逐张测试所有示例图片"""
    samples = sorted([
        f for f in os.listdir(SAMPLE_DIR)
        if f.endswith(('.jpg', '.png', '.jpeg'))
    ])

    assert len(samples) > 0, "没有找到示例图片"

    results = {}
    for name in samples:
        path = f"{SAMPLE_DIR}/{name}"
        with open(path, "rb") as f:
            img_bytes = f.read()
        b64 = base64.b64encode(img_bytes).decode()

        t0 = time.time()
        resp = requests.post(
            f"{API}/api/inspect",
            json={"image": b64, "conf_threshold": 0.25, "enable_sam": False},
            timeout=60,
        )
        elapsed = time.time() - t0

        assert resp.status_code == 200, f"{name}: HTTP {resp.status_code} — {resp.text[:200]}"

        data = resp.json()
        assert data["status"] == "completed", f"{name}: status={data['status']}"
        assert "defects" in data, f"{name}: missing defects"
        assert "summary" in data, f"{name}: missing summary"
        assert "annotated_image_b64" in data, f"{name}: missing annotated image"

        # 标注图应该是有效的 base64
        anno = data["annotated_image_b64"]
        assert len(anno) > 100, f"{name}: annotated image too small ({len(anno)} bytes)"

        summary = data["summary"]
        defects = data["defects"]

        results[name] = {
            "defects": len(defects),
            "total": summary["total"],
            "confirmed": summary["confirmed"],
            "critical": summary["critical"],
            "severity": summary["overall_severity"],
            "time_ms": data["processing_time_ms"],
            "elapsed_s": round(elapsed, 1),
        }

        print(f"  {name}: {len(defects)} defects, {summary['overall_severity']}, {elapsed:.1f}s")

    # 汇总
    print(f"\n总计: {len(samples)} 张图片全部通过")

    # 检查关键预期
    golden = [r for n, r in results.items() if "golden" in n]
    bridge = [r for n, r in results.items() if "bridge" in n]
    missing = [r for n, r in results.items() if "missing" in n]
    offset = [r for n, r in results.items() if "offset" in n and "missing" not in n]
    scratch = [r for n, r in results.items() if "scratch" in n]

    if golden:
        r = golden[0]
        print(f"  金板: {r['defects']} defects (期望 0) — {'✅' if r['defects'] == 0 else '⚠️'}")
    if bridge:
        r = bridge[0]
        print(f"  桥接: {r['defects']} defects, severity={r['severity']} — {'✅' if r['severity'] == 'CRITICAL' else '⚠️'}")

    return results


def test_chat_api():
    """测试 Agent 对话 API"""
    resp = requests.post(f"{API}/api/agent/chat", json={
        "message": "BGA焊点void率30%标准是多少？",
        "session_id": "test_e2e",
    }, timeout=30)
    assert resp.status_code == 200, f"Chat API failed: {resp.text[:200]}"
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 10
    print(f"  Chat: reply length={len(data['reply'])} ✅")


def test_knowledge_api():
    """测试知识库 API"""
    resp = requests.get(f"{API}/api/knowledge/stats", timeout=10)
    assert resp.status_code == 200
    stats = resp.json()
    print(f"  Knowledge: {stats.get('total_chunks', '?')} chunks")

    resp = requests.get(f"{API}/api/knowledge/search?q=焊点标准", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    print(f"  Search: {len(data.get('results', []))} results")


def test_report_api():
    """测试报告 API"""
    resp = requests.post(f"{API}/api/report/generate", json={
        "task_id": "test_e2e",
        "format": "md",
    }, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    print(f"  Report: id={data['report_id']} ✅")


if __name__ == "__main__":
    print("=== E2E 测试开始 ===\n")

    print("[1/4] 测试所有示例图片...")
    test_all_sample_images()

    print("\n[2/4] 测试 Agent 对话...")
    test_chat_api()

    print("\n[3/4] 测试知识库...")
    test_knowledge_api()

    print("\n[4/4] 测试报告生成...")
    test_report_api()

    print("\n=== 全部通过 ✅ ===")
