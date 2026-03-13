"""
Verify script for task1_data_science_tracker
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_science_tracker import ExperimentTracker

def test_basic_functionality():
    """测试基本功能"""
    tracker = ExperimentTracker()

    # 添加实验
    exp1 = tracker.add_experiment(
        name="exp1",
        dataset="mnist",
        model="cnn",
        accuracy=0.95,
        f1=0.93
    )
    assert exp1 is not None, "添加实验失败"

    # 检查实验数量
    assert len(tracker.experiments) == 1, f"期望1个实验，实际{len(tracker.experiments)}个"

    # 添加第二个实验
    tracker.add_experiment(
        name="exp2",
        dataset="cifar10",
        model="resnet",
        accuracy=0.92,
        f1=0.90
    )
    assert len(tracker.experiments) == 2, "添加第二个实验失败"

    print("✅ 基本功能测试通过")

def test_query_sorting():
    """测试查询排序"""
    tracker = ExperimentTracker()
    tracker.add_experiment("exp_a", "ds1", "model1", 0.85, 0.82)
    tracker.add_experiment("exp_b", "ds2", "model2", 0.92, 0.88)
    tracker.add_experiment("exp_c", "ds3", "model3", 0.78, 0.75)

    sorted_exps = tracker.get_experiments_sorted_by_accuracy()
    accuracies = [exp['accuracy'] for exp in sorted_exps]
    assert accuracies == sorted(accuracies, reverse=True), "排序不正确"
    assert accuracies[0] == 0.92, "最高准确率应为0.92"

    print("✅ 排序功能测试通过")

def test_average_accuracy():
    """测试平均准确率计算"""
    tracker = ExperimentTracker()
    tracker.add_experiment("exp1", "ds", "m", 0.80, 0.75)
    tracker.add_experiment("exp2", "ds", "m", 0.90, 0.85)
    tracker.add_experiment("exp3", "ds", "m", 0.70, 0.65)

    avg = tracker.get_average_accuracy()
    expected = round((0.80 + 0.90 + 0.70) / 3, 2)
    assert avg == expected, f"平均值计算错误: 期望{expected}, 实际{avg}"

    print("✅ 平均准确率测试通过")

def test_export_csv():
    """测试CSV导出"""
    tracker = ExperimentTracker()
    tracker.add_experiment("exp1", "mnist", "cnn", 0.95, 0.93)

    csv_file = "/tmp/test_export.csv"
    tracker.export_to_csv(csv_file)

    assert os.path.exists(csv_file), "CSV文件未生成"

    with open(csv_file, 'r') as f:
        content = f.read()
        assert "name,dataset,model,accuracy,f1" in content, "CSV缺少表头"
        assert "exp1" in content, "CSV缺少实验数据"

    os.remove(csv_file)
    print("✅ CSV导出测试通过")

def test_edge_cases():
    """测试边界条件"""
    tracker = ExperimentTracker()

    # 空列表平均值
    avg = tracker.get_average_accuracy()
    assert avg == 0.00, f"空列表平均值应为0.00，实际{avg}"

    # 空数据集名称
    try:
        tracker.add_experiment("exp_bad", "", "model", 0.5, 0.5)
        assert False, "应拒绝空数据集名称"
    except ValueError:
        pass

    # 准确率超出范围
    try:
        tracker.add_experiment("exp_bad2", "ds", "model", 1.5, 0.5)
        assert False, "应拒绝超出范围的准确率"
    except ValueError:
        pass

    print("✅ 边界条件测试通过")

if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_query_sorting()
        test_average_accuracy()
        test_export_csv()
        test_edge_cases()
        print("\n🎉 所有验证测试通过！")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
