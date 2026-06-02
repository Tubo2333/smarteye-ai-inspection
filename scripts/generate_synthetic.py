#!/usr/bin/env python
"""
合成 PCB 图像生成器

在没有真实 PCB 缺陷数据集的情况下，用 OpenCV 绘制模拟的 PCB 板
及其常见缺陷。生成的图片可用于:
1. YOLO 训练数据 (带自动标注)
2. Streamlit demo 示例图片
3. CV pipeline 功能验证
"""
import os
import sys
import json
import random
import cv2
import numpy as np
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

# 画布大小
CANVAS_W, CANVAS_H = 800, 600

# PCB 颜色
PCB_GREEN = (47, 107, 47)       # 深绿色基板
PCB_GREEN_VAR = (42, 97, 42)    # 变体
PAD_GOLD = (66, 170, 255)       # 金色焊盘
SOLDER_GRAY = (180, 180, 180)   # 锡膏灰色
TRACE_GREEN = (52, 130, 52)     # 铜线浅绿
COMPONENT_BLACK = (30, 30, 30)  # 芯片黑色
COMPONENT_BROWN = (60, 80, 140) # 电容棕色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# 随机种子
random.seed(42)
np.random.seed(42)


# ═══════════════════════════════════════════════════════════════
# 绘制基础 PCB
# ═══════════════════════════════════════════════════════════════

def draw_pcb_base() -> np.ndarray:
    """绘制基础 PCB 板（含基板、走线、焊盘、元件）"""
    img = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)

    # 基板
    color = tuple(c + random.randint(-8, 8) for c in PCB_GREEN)
    color = tuple(max(0, min(255, c)) for c in color)
    img[:, :] = color

    # 随机纹理
    noise = np.random.randint(-5, 5, (CANVAS_H, CANVAS_W, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # 走线 (若干水平/垂直的浅绿色线条)
    for _ in range(random.randint(15, 25)):
        if random.random() < 0.5:
            y = random.randint(20, CANVAS_H - 20)
            x1 = random.randint(10, CANVAS_W // 3)
            x2 = random.randint(CANVAS_W * 2 // 3, CANVAS_W - 10)
            cv2.line(img, (x1, y), (x2, y), TRACE_GREEN, 2)
        else:
            x = random.randint(20, CANVAS_W - 20)
            y1 = random.randint(10, CANVAS_H // 3)
            y2 = random.randint(CANVAS_H * 2 // 3, CANVAS_H - 10)
            cv2.line(img, (x, y1), (x, y2), TRACE_GREEN, 2)

    return img


def draw_pads_and_components(img: np.ndarray) -> list:
    """
    在 PCB 上绘制焊盘和元件。
    返回每个元件的: {bbox, center, size, type}
    """
    components = []

    for _ in range(random.randint(8, 15)):
        x = random.randint(80, CANVAS_W - 80)
        y = random.randint(80, CANVAS_H - 80)
        w = random.randint(30, 60)
        h = random.randint(20, 45)
        comp_type = random.choice(["chip", "cap", "resistor", "qfp"])

        # 绘制焊盘
        pad_margin = 8
        cv2.rectangle(img,
                      (x - pad_margin, y - pad_margin),
                      (x + w + pad_margin, y - 2),
                      PAD_GOLD, -1)
        cv2.rectangle(img,
                      (x - pad_margin, y + h + 2),
                      (x + w + pad_margin, y + h + pad_margin),
                      PAD_GOLD, -1)

        components.append({
            "bbox": [x, y, x + w, y + h],
            "center": (x + w // 2, y + h // 2),
            "size": (w, h),
            "type": comp_type,
        })

    return components


def draw_components_on_pads(img: np.ndarray, components: list):
    """在焊盘上绘制元件本体"""
    for comp in components:
        x, y, x2, y2 = comp["bbox"]
        comp_type = comp["type"]

        if comp_type in ("chip", "qfp"):
            color = COMPONENT_BLACK
        elif comp_type == "cap":
            color = COMPONENT_BROWN
        else:
            color = tuple(c + random.randint(-10, 10) for c in (80, 80, 160))

        color = tuple(max(0, min(255, c)) for c in color)
        cv2.rectangle(img, (x, y), (x2, y2), color, -1)

        # 丝印标记
        cv2.putText(img, f"C{random.randint(1,99)}",
                    (x + 2, y - 6), cv2.FONT_HERSHEY_SIMPLEX,
                    0.35, WHITE, 1)

    return img


# ═══════════════════════════════════════════════════════════════
# 绘制缺陷
# ═══════════════════════════════════════════════════════════════

def add_bridge_defect(img: np.ndarray, components: list) -> dict:
    """
    桥接缺陷: 在两个相邻焊盘之间画一条锡桥
    返回 YOLO 格式的标注
    """
    if len(components) < 2:
        return None

    # 找两个相邻元件
    comp_a = random.choice(components)
    others = [c for c in components if c != comp_a]
    comp_b = min(others, key=lambda c: np.sqrt(
        (c["center"][0] - comp_a["center"][0])**2 +
        (c["center"][1] - comp_a["center"][1])**2
    ))

    ax, ay, ax2, ay2 = comp_a["bbox"]
    bx, by, bx2, by2 = comp_b["bbox"]

    # 在两个元件相邻焊盘间画桥接线
    bridge_x1 = (ax2 + bx) // 2
    bridge_y1 = (ay + by2) // 2
    bridge_x2 = bridge_x1 + random.randint(30, 80)
    bridge_y2 = bridge_y1 + random.randint(5, 15)

    cv2.line(img, (bridge_x1, bridge_y1), (bridge_x2, bridge_y2),
             SOLDER_GRAY, thickness=random.randint(4, 8))

    # 计算 bbox (扩大一点)
    x1 = min(bridge_x1, bridge_x2) - 10
    y1 = min(bridge_y1, bridge_y2) - 10
    x2 = max(bridge_x1, bridge_x2) + 10
    y2 = max(bridge_y1, bridge_y2) + 10

    return {
        "bbox": [max(0, x1), max(0, y1), min(CANVAS_W, x2), min(CANVAS_H, y2)],
        "class": "bridge",
    }


def add_missing_component(img: np.ndarray, components: list) -> dict:
    """缺件缺陷: 移除一个元件，留下空焊盘"""
    if not components:
        return None

    comp = random.choice(components)
    x, y, x2, y2 = comp["bbox"]

    # 用 PCB 基板色覆盖元件
    color = tuple(c + random.randint(-5, 5) for c in PCB_GREEN)
    color = tuple(max(0, min(255, c)) for c in color)
    cv2.rectangle(img, (x, y), (x2, y2), color, -1)

    # 保留焊盘但加一点变色（氧化痕迹）
    overlay = img[y:y2, x:x2].copy()
    cv2.addWeighted(overlay, 0.7,
                    np.full_like(overlay, PCB_GREEN_VAR), 0.3, 0,
                    img[y:y2, x:x2])

    return {
        "bbox": comp["bbox"],
        "class": "missing_component",
    }


def add_offset_defect(img: np.ndarray, components: list) -> dict:
    """偏移缺陷: 将一个元件画在偏移位置"""
    if not components:
        return None

    comp = random.choice(components)
    x, y, x2, y2 = comp["bbox"]
    w, h = x2 - x, y2 - y

    # 用基板色覆盖原位置
    color = tuple(c + random.randint(-5, 5) for c in PCB_GREEN)
    color = tuple(max(0, min(255, c)) for c in color)
    cv2.rectangle(img, (x, y), (x2, y2), color, -1)

    # 偏移量 (元件尺寸的 15-30%)
    dx = int(w * random.uniform(0.15, 0.30) * random.choice([-1, 1]))
    dy = int(h * random.uniform(0.15, 0.30) * random.choice([-1, 1]))

    nx, ny = x + dx, y + dy
    nx2, ny2 = x2 + dx, y2 + dy

    # 重绘偏移后的元件
    comp_color = COMPONENT_BLACK if comp["type"] in ("chip", "qfp") else COMPONENT_BROWN
    cv2.rectangle(img, (nx, ny), (nx2, ny2), comp_color, -1)

    return {
        "bbox": [max(0, nx-5), max(0, ny-5), min(CANVAS_W, nx2+5), min(CANVAS_H, ny2+5)],
        "class": "offset",
    }


def add_solder_defect(img: np.ndarray, components: list) -> dict:
    """少锡缺陷: 移除/缩小一个焊盘上的锡膏"""
    if not components:
        return None

    comp = random.choice(components)
    x, y, x2, y2 = comp["bbox"]

    # 焊盘位置在元件上下方
    pad_h = 8
    pad_y_top = y - pad_h - 2
    pad_y_bot = y2 + 2

    # 用基板色部分覆盖焊盘（模拟少锡）
    if random.random() < 0.5 and pad_y_top > 0:
        # 少锡 - 缩小焊盘
        insuf_x = x + random.randint(5, 15)
        insuf_w = max(5, (x2 - x) - random.randint(15, 30))
        cv2.rectangle(img,
                      (insuf_x, pad_y_top),
                      (x2, pad_y_top + pad_h),
                      PCB_GREEN_VAR, -1)
        bbox = [insuf_x, pad_y_top - 2, x2, pad_y_top + pad_h + 2]
    elif pad_y_bot + pad_h < CANVAS_H:
        cv2.rectangle(img,
                      (x, pad_y_bot),
                      (x + (x2-x)//2, pad_y_bot + pad_h),
                      PCB_GREEN_VAR, -1)
        bbox = [x, pad_y_bot - 2, x + (x2-x)//2, pad_y_bot + pad_h + 2]
    else:
        return None

    return {
        "bbox": [max(0, bbox[0]), max(0, bbox[1]), min(CANVAS_W, bbox[2]), min(CANVAS_H, bbox[3])],
        "class": "insufficient_solder",
    }


def add_scratch_defect(img: np.ndarray, components: list = None) -> dict:
    """划伤缺陷: 在 PCB 表面画一条划痕"""
    start_x = random.randint(50, CANVAS_W - 200)
    start_y = random.randint(50, CANVAS_H - 50)
    length = random.randint(60, 200)
    angle = random.uniform(-0.5, 0.5)

    end_x = start_x + int(length * np.cos(angle))
    end_y = start_y + int(length * np.sin(angle))

    # 白色划痕 + 深色边缘（模拟铜箔暴露）
    cv2.line(img, (start_x, start_y), (end_x, end_y),
             (200, 200, 220), thickness=2)
    cv2.line(img, (start_x, start_y), (end_x, end_y),
             (180, 140, 100), thickness=1)

    x1 = min(start_x, end_x) - 8
    y1 = min(start_y, end_y) - 8
    x2 = max(start_x, end_x) + 8
    y2 = max(start_y, end_y) + 8

    return {
        "bbox": [max(0, x1), max(0, y1), min(CANVAS_W, x2), min(CANVAS_H, y2)],
        "class": "scratch",
    }


# ═══════════════════════════════════════════════════════════════
# 主生成函数
# ═══════════════════════════════════════════════════════════════

def generate_golden_board() -> np.ndarray:
    """生成完美金板"""
    img = draw_pcb_base()
    comps = draw_pads_and_components(img)
    draw_components_on_pads(img, comps)
    return img


def generate_defect_image(defect_type: str) -> tuple:
    """
    生成带指定缺陷的 PCB 图片
    返回: (image, labels_dict)
    """
    img = draw_pcb_base()
    comps = draw_pads_and_components(img)
    draw_components_on_pads(img, comps)

    label = None

    if defect_type == "bridge":
        label = add_bridge_defect(img, comps)
    elif defect_type == "missing_component":
        label = add_missing_component(img, comps)
    elif defect_type == "offset":
        label = add_offset_defect(img, comps)
    elif defect_type == "insufficient_solder":
        label = add_solder_defect(img, comps)
    elif defect_type == "scratch":
        label = add_scratch_defect(img)
    elif defect_type == "mixed":
        # 混合: 随机 2-3 种缺陷
        defects = [add_bridge_defect, add_offset_defect, add_solder_defect, add_scratch_defect]
        chosen = random.sample(defects, random.randint(2, 3))
        label = None
        for fn in chosen:
            result = fn(img, comps)
            if result and label is None:
                label = result  # 用第一个缺陷的 bbox

    return img, label


def save_sample_images(output_dir: str = "data/sample_images"):
    """生成并保存所有示例图片和 YOLO 标注"""
    os.makedirs(output_dir, exist_ok=True)

    generated = []

    # 1. 金板
    golden = generate_golden_board()
    cv2.imwrite(f"{output_dir}/pcb_golden.jpg", golden)

    # 2. 各种缺陷
    defect_types = ["bridge", "missing_component", "offset", "insufficient_solder", "scratch", "mixed"]

    for dtype in defect_types:
        img, label = generate_defect_image(dtype)
        filename = f"pcb_defect_{dtype}.jpg"
        cv2.imwrite(f"{output_dir}/{filename}", img)
        generated.append({"file": filename, "type": dtype, "label": label})

    # 3. 多生成几张不同随机种子的混合缺陷图
    for i in range(3):
        random.seed(100 + i)
        np.random.seed(100 + i)
        img, _ = generate_defect_image("mixed")
        filename = f"pcb_defect_mixed_{i+1}.jpg"
        cv2.imwrite(f"{output_dir}/{filename}", img)
        generated.append({"file": filename, "type": "mixed", "label": None})

    # 保存标注信息
    with open(f"{output_dir}/_labels.json", "w") as f:
        json.dump(generated, f, ensure_ascii=False, indent=2)

    print(f"[OK] Generated {len(generated) + 1} images in {output_dir}/")
    print(f"     - pcb_golden.jpg (金板)")
    for g in generated:
        label_str = f"bbox={g['label']['bbox']}" if g['label'] else "unlabeled"
        print(f"     - {g['file']} ({g['type']}, {label_str})")


def generate_yolo_dataset(output_dir: str = "data/pcb_dataset", n_samples: int = 200):
    """
    生成 YOLO 格式的训练数据集。

    目录结构:
      data/pcb_dataset/
        images/train/  (80%)
        images/val/    (20%)
        labels/train/  (YOLO txt)
        labels/val/
        data.yaml
    """
    os.makedirs(f"{output_dir}/images/train", exist_ok=True)
    os.makedirs(f"{output_dir}/images/val", exist_ok=True)
    os.makedirs(f"{output_dir}/labels/train", exist_ok=True)
    os.makedirs(f"{output_dir}/labels/val", exist_ok=True)

    # 类别映射
    class_map = {
        "bridge": 0,
        "missing_component": 1,
        "offset": 2,
        "insufficient_solder": 3,
        "scratch": 4,
    }

    img_count = 0
    train_count = int(n_samples * 0.8)

    defect_types_list = list(class_map.keys())

    for i in range(n_samples):
        # 80% 单缺陷, 20% 多缺陷
        if random.random() < 0.8:
            defect_type = random.choice(defect_types_list)
        else:
            defect_type = "mixed"

        # 随机种子保证多样性
        seed = 1000 + i
        random.seed(seed)
        np.random.seed(seed)

        img, label = generate_defect_image(defect_type)

        split = "train" if i < train_count else "val"
        img_name = f"pcb_{i:04d}.jpg"
        label_name = f"pcb_{i:04d}.txt"

        cv2.imwrite(f"{output_dir}/images/{split}/{img_name}", img)

        # 写 YOLO 标注
        with open(f"{output_dir}/labels/{split}/{label_name}", "w") as f:
            if defect_type == "mixed":
                # 为混合缺陷写多个标注 (简化: 写主缺陷)
                if label and label.get("bbox"):
                    cls_id = class_map.get(label["class"], 0)
                    x1, y1, x2, y2 = label["bbox"]
                    x_center = ((x1 + x2) / 2) / CANVAS_W
                    y_center = ((y1 + y2) / 2) / CANVAS_H
                    w = (x2 - x1) / CANVAS_W
                    h = (y2 - y1) / CANVAS_H
                    f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
            else:
                cls_id = class_map.get(defect_type, 0)
                if label and label.get("bbox"):
                    x1, y1, x2, y2 = label["bbox"]
                    x_center = ((x1 + x2) / 2) / CANVAS_W
                    y_center = ((y1 + y2) / 2) / CANVAS_H
                    w = (x2 - x1) / CANVAS_W
                    h = (y2 - y1) / CANVAS_H
                    f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")

        img_count += 1
        if (img_count) % 50 == 0:
            print(f"  ... {img_count}/{n_samples} images generated")

    # 写 data.yaml
    yaml_content = f"""# PCB Defect Dataset (Synthetic)
path: {os.path.abspath(output_dir)}
train: images/train
val: images/val

nc: 5
names:
  0: bridge
  1: missing_component
  2: offset
  3: insufficient_solder
  4: scratch
"""
    with open(f"{output_dir}/data.yaml", "w") as f:
        f.write(yaml_content)

    print(f"\n[OK] YOLO dataset generated: {output_dir}/")
    print(f"     Total: {n_samples} images ({train_count} train / {n_samples - train_count} val)")
    print(f"     Classes: {list(class_map.keys())}")
    print(f"     Config: {output_dir}/data.yaml")


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="合成 PCB 图像生成器")
    parser.add_argument("--samples", action="store_true", help="生成示例图片 (6张)")
    parser.add_argument("--dataset", action="store_true", help="生成 YOLO 训练数据集")
    parser.add_argument("--n", type=int, default=200, help="训练数据集图片数量")
    parser.add_argument("-o", type=str, default=None, help="输出目录")

    args = parser.parse_args()

    if not args.samples and not args.dataset:
        # 默认: 只生成示例图片
        args.samples = True

    if args.samples:
        out = args.o or "data/sample_images"
        save_sample_images(out)

    if args.dataset:
        out = args.o or "data/pcb_dataset"
        generate_yolo_dataset(out, n_samples=args.n)
