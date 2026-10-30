# Lab 1 实验报告

- 学生：潘孝圆，24300240128。
- 报告：`24300240128-lab1.pdf`，LaTeX 源码：`report.tex`。
- `evidence/student-run.log`：学生提供的原始运行输出，Usage 为 1144。
- `evidence/run-1.log` 至 `run-3.log`：报告整理阶段辅助执行的三次独立 QEMU 运行。
- `evidence/verification.json`：运行结果和对应代码的 SHA-256。

在本目录编译：

```bash
mkdir -p .latex-build
xelatex -interaction=nonstopmode -halt-on-error -output-directory=.latex-build -jobname=24300240128-lab1 report.tex
cp .latex-build/24300240128-lab1.pdf 24300240128-lab1.pdf
```

报告中的 AI 使用说明根据实际教学、关键调用示例、代码检查、手动编写与运行反馈整理。
