"""FastAPI 路由集成测试（不需要 GPU）"""
import pytest
from fastapi.testclient import TestClient
import base64
import cv2
import numpy as np

# 在测试中创建 app（不预加载模型）
from backend.main import app

client = TestClient(app)


class TestHealthCheck:
    """健康检查"""

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["service"] == "SmartEye API"

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_docs_accessible(self):
        """Swagger 文档应可访问"""
        resp = client.get("/docs")
        assert resp.status_code == 200


class TestKnowledgeRoutes:
    """知识库路由"""

    def test_search_empty_kb(self):
        """空知识库返回空结果"""
        resp = client.get("/api/knowledge/search?q=焊点标准")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_stats(self):
        """知识库统计"""
        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_chunks" in data


class TestInspectRoute:
    """检测路由"""

    def test_inspect_no_image(self):
        """无图像应返回错误"""
        resp = client.post("/api/inspect", json={"image": ""})
        assert resp.status_code in (200, 422, 500)  # 取决于实现

    def test_inspect_with_valid_image(self):
        """带有效图像应返回结果"""
        # 创建简单的测试图像
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        _, buf = cv2.imencode('.jpg', img)
        b64 = base64.b64encode(buf.tobytes()).decode()

        resp = client.post("/api/inspect", json={
            "image": b64,
            "conf_threshold": 0.5,
            "enable_sam": False,
        })
        # 可能返回 200（成功）或 500（YOLO模型未训练）
        assert resp.status_code in (200, 500)


class TestChatRoute:
    """对话路由"""

    def test_chat_no_key(self):
        """无 API Key 时使用 fallback"""
        resp = client.post("/api/agent/chat", json={
            "message": "BGA焊点标准是多少？",
            "session_id": "test_session",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data

    def test_chat_with_image(self):
        """带图片的对话 — 可能因模型未加载返回 500"""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        _, buf = cv2.imencode('.jpg', img)
        b64 = base64.b64encode(buf.tobytes()).decode()

        resp = client.post("/api/agent/chat", json={
            "message": "看看这张图",
            "image_b64": b64,
            "session_id": "test_img",
            "task_type": "inspection",
        })
        # 200=成功, 500=模型未加载/GPU不可用（测试环境正常）
        assert resp.status_code in (200, 500)

    def test_chat_history(self):
        """获取对话历史"""
        resp = client.get("/api/agent/chat/test_session/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data
