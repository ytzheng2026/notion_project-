"""
Data Science Tracker implementation
"""

class ExperimentTracker:
    def __init__(self):
        self.experiments = []

    def add_experiment(self, name, dataset, model, accuracy, f1):
        """添加新实验"""
        # 验证输入
        if not name or not dataset:
            raise ValueError("实验名称和数据集名称不能为空")
        if not (0 <= accuracy <= 1):
            raise ValueError("准确率必须在0-1范围内")
        if not (0 <= f1 <= 1):
            raise ValueError("F1分数必须在0-1范围内")

        experiment = {
            'name': name,
            'dataset': dataset,
            'model': model,
            'accuracy': round(float(accuracy), 4),
            'f1': round(float(f1), 4)
        }
        self.experiments.append(experiment)
        return experiment

    def get_experiments_sorted_by_accuracy(self):
        """按准确率降序排序返回实验列表"""
        return sorted(self.experiments, key=lambda x: x['accuracy'], reverse=True)

    def get_average_accuracy(self):
        """计算平均准确率，保留两位小数"""
        if not self.experiments:
            return 0.00
        avg = sum(exp['accuracy'] for exp in self.experiments) / len(self.experiments)
        return round(avg, 2)

    def export_to_csv(self, filepath):
        """导出实验数据为CSV"""
        import csv
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['name', 'dataset', 'model', 'accuracy', 'f1']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for exp in self.experiments:
                writer.writerow(exp)
