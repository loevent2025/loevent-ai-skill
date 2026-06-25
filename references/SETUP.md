# SETUP —— 给 agent 跑的环境 runbook(平台无关)

目标:让用户的 AI 助手帮他在本机把环境配好,之后任何 LoEvent skill 都能用一个 Gemini Key 跑。

1. **检查 Python**(≥3.11),建虚拟环境:
   ```bash
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **配 Key**:把 `.env.example` 复制成 `.env`,填入用户自己的 `GEMINI_API_KEY`
   (在 https://aistudio.google.com/apikey 申请)。也可直接 `export GEMINI_API_KEY=AIza...`。
3. **自检**:
   ```bash
   python engine/doctor.py
   ```
   它会:验 Key → 探文本模型 → 探 Google Search grounding(走 gemini-3.5-flash)→ 探图像档权限 → 提示 OCR/地图需另配。
4. **缺权限自动降级**:doctor 报图像档/Vision 不可用时,海报类步骤标「跳过/降级」,**文本类 skill 照常跑**。
5. **工作目录**:同一个活动的所有 skill 共用一个目录(用 `LOEVENT_WORKDIR` 指定,缺省当前目录)。
   - 先跑 `skill-init` 把活动描述抽成 `event/host/plan.json`;
   - 其它 skill 从这几个文件读上下文、把自己的结果写回工作目录(如 `audience.json` 并 merge 进 `plan.json`)。
   - 没有真实活动时,可把 `templates/` 下的样本档复制进工作目录先试跑。

> 这一份不是给人读的安装文档,是给 **agent** 照着执行的 runbook:它读完应能自动建 venv、配 Key、过 doctor、再跑第一条 skill。
