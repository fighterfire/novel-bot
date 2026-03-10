"""WebUI API 功能测试脚本"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'

def test_webui():
    """测试 WebUI 后端所有功能"""
    
    print("\n" + "="*60)
    print("🧪 WebUI 后端 API 功能测试")
    print("="*60)
    
    # 测试 1: 健康检查
    print("\n[1/5] 健康检查...")
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        print("  ✅ 健康检查通过")
    except Exception as e:
        print(f"  ❌ 健康检查失败: {e}")
        return False
    
    # 测试 2: 创建任务
    print("\n[2/5] 创建任务...")
    try:
        response = requests.post(f'{BASE_URL}/api/tasks', json={
            'phase': 'outline',
            'setting_file': 'presets/ai_love_story.yaml',
            'output_dir': 'output/test',
            'dry_run': True
        }, timeout=5)
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data.get('task_id')
        assert task_id
        print(f"  ✅ 任务创建成功")
        print(f"     任务ID: {task_id[:16]}...")
    except Exception as e:
        print(f"  ❌ 任务创建失败: {e}")
        return False
    
    # 等待任务执行
    time.sleep(2)
    
    # 测试 3: 获取任务信息
    print("\n[3/5] 获取任务信息...")
    try:
        response = requests.get(f'{BASE_URL}/api/tasks/{task_id}', timeout=5)
        assert response.status_code == 200
        task_info = response.json()
        
        # 验证任务信息结构
        required_fields = ['task_id', 'phase', 'status', 'progress', 'logs']
        for field in required_fields:
            assert field in task_info, f"缺少字段: {field}"
        
        print(f"  ✅ 任务信息获取成功")
        print(f"     状态: {task_info.get('status')}")
        print(f"     进度: {task_info.get('progress')}%")
        print(f"     阶段: {task_info.get('phase')}")
        print(f"     日志数: {len(task_info.get('logs', []))}")
    except Exception as e:
        print(f"  ❌ 任务信息获取失败: {e}")
        return False
    
    # 测试 4: 获取任务日志
    print("\n[4/5] 获取任务日志...")
    try:
        response = requests.get(f'{BASE_URL}/api/tasks/{task_id}/logs', timeout=5)
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        
        print(f"  ✅ 日志获取成功")
        print(f"     总日志条数: {len(logs)}")
        if logs:
            print(f"     样本日志:")
            for log in logs[-2:]:
                print(f"       [{log.get('level')}] {log.get('message')}")
    except Exception as e:
        print(f"  ❌ 日志获取失败: {e}")
        return False
    
    # 测试 5: 多任务创建
    print("\n[5/5] 多任务创建测试...")
    try:
        task_ids = []
        for i in range(3):
            response = requests.post(f'{BASE_URL}/api/tasks', json={
                'phase': 'setting_pack',
                'setting_file': 'presets/test.yaml',
                'output_dir': f'output/test_{i}',
                'dry_run': True
            }, timeout=5)
            assert response.status_code == 200
            task_ids.append(response.json()['task_id'])
        
        print(f"  ✅ 多任务创建成功")
        print(f"     创建了 {len(task_ids)} 个任务")
    except Exception as e:
        print(f"  ❌ 多任务创建失败: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ 全部测试通过！WebUI 后端运行正常")
    print("="*60)
    return True


if __name__ == '__main__':
    import sys
    success = test_webui()
    sys.exit(0 if success else 1)
