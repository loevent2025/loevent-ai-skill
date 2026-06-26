"""契约测试:守住 #1(scene_type/event_scale 跨 skill 字段约定)。

init 把 scene_type/event_scale 写在 plan 顶层,且 ai_extracted 非空但不含这两个字段。
timeline 必须从顶层读到真值,不能因为 ai_extracted 存在就退化成默认值。
字段一旦再错位(死分支回归),这个测试立刻红——这正是当初漏掉 #1 的失败模式。
"""


def test_timeline_reads_scene_type_from_plan_toplevel(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    # ← init 真实产出形态
    plan = {
        "scene_type": "developer_meetups",
        "event_scale": "small",
        "ai_extracted": {"goal": "拉开发者", "content": "demo+workshop", "guests": []},
    }
    _, scene_type, event_scale = timeline._build_prompt_vars(plan, {"host_profile": ""})
    assert scene_type == "developer_meetups", "退化成默认值了 = #1 回归"
    assert event_scale == "small", "退化成默认值了 = #1 回归"


def test_timeline_defaults_only_when_truly_missing(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    plan = {"ai_extracted": {"goal": "x"}}  # 真的两个字段都没有
    _, scene_type, event_scale = timeline._build_prompt_vars(plan, {})
    assert scene_type == "business_conferences"
    assert event_scale == "medium"


def test_timeline_flat_plan_path(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    plan = {"scene_type": "hackathons", "event_scale": "large", "eventType": "x"}
    _, scene_type, event_scale = timeline._build_prompt_vars(plan, {})
    assert scene_type == "hackathons"
    assert event_scale == "large"
