# Lab 0 实验报告

- 学生：潘孝圆，24300240128。
- 提交文件：`24300240128-lab0.pdf`。
- 可编辑源码：`report.tex`。
- 当前 PDF 为一页 A4 简版，只保留三个任务的思路、逐步教学对话摘要和简短运行结果，不包含环境配置或扩展测试章节。
- `figures/`：实际命令输出展示页的浏览器截图；不是桌面终端的直接截屏。
- `evidence/`：版本信息、编译与 QEMU 输出、ELF 布局及 BSS 清零检查的原始日志。
- `scripts/`：报告整理阶段使用的辅助采集与验证脚本，不参与内核构建。

## 编译报告

在本目录执行：

```bash
mkdir -p .latex-build
xelatex -interaction=nonstopmode -halt-on-error -output-directory=.latex-build -jobname=24300240128-lab0 report.tex
cp .latex-build/24300240128-lab0.pdf 24300240128-lab0.pdf
```

依赖 XeLaTeX、ctex、fontspec、xcolor，以及 AR PL SungtiL GB、Droid Sans Fallback、DejaVu 系列字体。

## 留存的原始资料与辅助验证

以下日志、截图和脚本作为过程资料保留，当前一页报告不再展开这些内容。

在仓库根目录执行：

```bash
/usr/bin/python3 docs/lab0/scripts/collect_evidence.py
gdb-multiarch --nx --batch -x docs/lab0/scripts/verify_bss.gdb > docs/lab0/evidence/bss-check.log 2>&1
/usr/bin/python3 docs/lab0/scripts/render_evidence.py
```

采集脚本会构建镜像、启动 QEMU，在四行 Hello 出现后通过伪终端发送 `Ctrl+A`、`x` 退出。
BSS 检查脚本在独立调试运行中临时改写内存，在 `memset` 前填入 `0xA5`，并在 `smp_init()` 调用前检查全部清零；不修改内核源码或链接脚本。
该脚本的停止位置对应当前 `src/main.c:15`。若源码行号变化，先更新断点位置。
截图脚本需要本机的 Google Chrome 无头模式，仅截取本地页面中的真实日志内容，不访问外部网页。

`evidence/initial-run.log` 保存学生先前粘贴的实际终端输出，其 `core` 为小写；`evidence/qemu.log` 为改成 `Core` 后的重新验证结果。报告没有将两次运行混为一次。

报告在每个任务中简述了提问、逐步讲解、关键调用示例和本人手动修改的过程，末尾注明工具与模型标识。
