# 人生自传成书 / Autobiography Studio

一个隐私优先、证据驱动的 Agent Skill：把本人主动提供的朋友圈导出内容、日记、文件、照片和访谈，整理为带封面、目录、Word 与 PDF 的个人自传。

![SkillHub listing cover](marketplace/listing-cover.png)

## 它能做什么

- 盘点本人主动提供的资料，不登录微信或其他私人账号
- 建立时间线、人物表、事实卡、冲突项和隐私决定
- 根据素材缺口开展多轮访谈，而不是机械地照问卷提问
- 提供朴实克制、温暖家庭、文学非虚构、事业历程、口述史五种风格模板
- 在获得允许后搜索本人公开信息，识别同名风险并逐条确认
- 生成书名、目录、章节、封面方案、Word 和 PDF
- 在交付前检查事实、隐私、目录、版式以及文件真实性

## 隐私边界

这个 Skill：

- 只用于用户本人写自传
- 只处理用户主动上传、粘贴或指定的本地材料
- 不索要密码、Cookie、Token、扫码登录或账号会话
- 不自动抓取朋友圈、邮箱、网盘或社交平台
- 不把私人资料发送到本项目维护者的服务器
- 不把同名人物的公开信息直接写入自传
- 不虚构经历、对白、证书、头衔、荣誉或公共事件

运行时是否使用宿主提供的联网搜索、生图、文档或 PDF 能力，由用户确认和宿主配置决定。

## 安装

### SkillHub

在 SkillHub 搜索「人生自传成书」，或从本仓库 Release 下载 `autobiography-studio-1.0.0.zip` 后导入。

### Codex / Agent Skills 兼容宿主

把 `autobiography-studio/` 目录安装到宿主的 Skills 目录。该目录根部必须保留 `SKILL.md`。

## 示例指令

```text
使用 $autobiography-studio 帮我整理这些朋友圈导出内容和日记，先盘点，再访谈补齐，最后做成家庭版自传。
```

```text
我想写一部朴实克制的个人自传。请先建立时间线，标出缺失年份，再围绕童年、事业转折和价值观逐轮访谈我。
```

```text
这些是我提供的简历、照片和文章。可以搜索我的公开报道，但任何搜索结果写入正文前都要先让我确认。
```

## 输出结构

典型项目会包含：

```text
my-autobiography/
├── project-status.json
├── material-index.json
├── timeline.md
├── people.md
├── fact-ledger.md
├── interview-notes.md
├── privacy-decisions.md
├── sources.md
├── manuscript.md
└── output/
    ├── book.docx
    ├── book.pdf
    └── cover.png
```

Word 与 PDF 输出依赖宿主具备真实的文档创建和 PDF 生成/渲染能力。若宿主缺少这些能力，Skill 会保留手稿源文件并明确提示，不会用改后缀的方式伪造文件。

## 本地工具

素材清单：

```powershell
python autobiography-studio/scripts/inventory_materials.py <素材目录> --output <项目目录>/material-index.json
```

项目确认门校验：

```powershell
python autobiography-studio/scripts/validate_project.py <项目目录> --stage draft
python autobiography-studio/scripts/validate_project.py <项目目录> --stage final
```

构建 SkillHub ZIP：

```powershell
powershell -ExecutionPolicy Bypass -File tools/package_skill.ps1
```

## 开发验证

```powershell
python -m unittest discover -s tests -v
$env:PYTHONUTF8=1
python C:\Users\Cao\.codex\skills\.system\skill-creator\scripts\quick_validate.py autobiography-studio
```

测试数据必须是虚构数据。不要把真实日记、朋友圈内容、证件、照片或生成的私人自传提交到 Git。

## 许可

[MIT License](LICENSE)
