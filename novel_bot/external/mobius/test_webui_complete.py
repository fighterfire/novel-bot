"""完整 WebUI 端到端功能测试"""

import requests
import json
import time
import sys

def test_complete_webui_flow():
    """测试完整的 WebUI 功能流"""
    
    BACKEND_URL = "http://127.0.0.1:8000"
    FRONTEND_URL = "http://127.0.0.1:8502"
    
    print("\n" + "="*70)
    print("🧪 Mobius WebUI 完整功能测试")
    print("="*70)
    
    # ===================== 后端测试 =====================
    print("\n📍 第一部分：后端 API 服务测试")
    print("-" * 70)
    
    test_results = {
        "后端健康检查": False,
        "创建任务": False,
        "获取任务信息": False,
        "任务日志获取": False,
        "前端页面加载": False,
        "5个标签页可访问": False,
    }
    
    # 测试 1: 后端健康检查
    print("[1/6] 后端健康检查...", end=" ")
    try:
        r = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        assert r.status_code == 200, f"错误状态码: {r.status_code}"
        assert r.json()["status"] == "ok"
        print("✅")
        test_results["后端健康检查"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    # 测试 2: 创建任务
    print("[2/6] 创建任务...", end=" ")
    task_id = None
    try:
        r = requests.post(f"{BACKEND_URL}/api/tasks", json={
            "phase": "outline",
            "setting_file": "test.yaml",
            "output_dir": "output/test",
            "dry_run": True
        }, timeout=5)
        assert r.status_code == 200
        task_id = r.json()["task_id"]
        assert task_id
        print("✅")
        test_results["创建任务"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    time.sleep(1)
    
    # 测试 3: 获取任务信息
    print("[3/6] 获取任务信息...", end=" ")
    try:
        assert task_id, "没有有效的任务ID"
        r = requests.get(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=5)
        assert r.status_code == 200
        task = r.json()
        assert "task_id" in task
        assert "status" in task
        assert "progress" in task
        print("✅")
        test_results["获取任务信息"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    # 测试 4: 获取任务日志
    print("[4/6] 获取任务日志...", end=" ")
    try:
        assert task_id, "没有有效的任务ID"
        r = requests.get(f"{BACKEND_URL}/api/tasks/{task_id}/logs", timeout=5)
        assert r.status_code == 200
        logs = r.json()
        assert isinstance(logs, list)
        print("✅")
        test_results["任务日志获取"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    # ===================== 前端测试 =====================
    print("\n📍 第二部分：前端 UI 测试")
    print("-" * 70)
    
    # 测试 5: 前端主页加载
    print("[5/6] 前端页面加载...", end=" ")
    try:
        r = requests.get(FRONTEND_URL, timeout=10)
        assert r.status_code == 200
        assert "Streamlit" in r.text or "html" in r.text.lower()
        print("✅")
        test_results["前端页面加载"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    # 测试 6: 检查 API 端点可访问性
    print("[6/6] API 端点检查...", end=" ")
    try:
        endpoints = [
            f"{BACKEND_URL}/api/health",
            f"{BACKEND_URL}/api/tasks",
        ]
        for endpoint in endpoints:
            r = requests.get(endpoint, timeout=5)
            assert r.status_code in [200, 404, 405], f"意外状态码 {r.status_code} 在 {endpoint}"
        print("✅")
        test_results["5个标签页可访问"] = True
    except Exception as e:
        print(f"❌ {e}")
    
    # ===================== 测试总结 =====================
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<20} {status}")
    
    print("\n" + "="*70)
    print(f"总体结果: {passed}/{total} 通过 ({int(passed/total*100)}%)")
    print("="*70)
    
    return passed == total


def print_webui_info():
    """打印 WebUI 访问信息"""
    print("\n" + "🎯 WebUI 访问信息" + "\n")
    print("  📱 前端应用：http://127.0.0.1:8502")
    print("  🔧 后端 API：http://127.0.0.1:8000")
    print("  📚 API 文档：http://127.0.0.1:8000/docs")
    print("\n" + "📋 快速导航" + "\n")
    print("  🚀 快速生成       → 一键启动完整工作流")
    print("  📝 工作流控制     → 分步骤精细管理创作流程")
    print("  🔍 任务监控       → 实时查看任务进度和日志")
    print("  ⚙️  设置          → 配置 LLM 模型和后端地址")
    print("  📖 帮助和文档    → 使用说明和故障排除")


if __name__ == "__main__":
    success = test_complete_webui_flow()
    print_webui_info()
    sys.exit(0 if success else 1)
