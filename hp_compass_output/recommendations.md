# HP Compass Recommendations

This report is generated from AMPlify HP records. It supports the existing wet-lab, dry-lab, software, safety, education, and wiki materials by identifying unclosed feedback loops.

## 1. 西北农林科技大学资环学院钱勋教授

- Source: `20260527_钱勋教授访谈_HP小循环_主线优化版_JU_Krakow风格_中文版（修改）.docx`
- Status: `L3_Evidenced`
- Priority: `0.855`
- Categories: Safety, Model, Problem Definition, Environment, Software
- Next step: 建议在后续回访中，向钱勋教授展示 PDES 模型的初步验证结果，并探讨如何将环境降解预测与现有粪污处理工艺结合，以增强模型的实际应用价值。
- Materials: PDES 模型的技术说明与初步验证数据, AMPlify 软件中 Environmental Degradation Panel 的界面截图, 项目更新后的安全表述文档, 关于环境抗性基因背景的文献综述
- Suggested questions:
  - 您认为 PDES 模型中的哪些参数最需要结合真实环境数据校准？
  - 在养殖粪污处理流程中，哪个环节最适合引入抗菌肽降解评估？
  - 您对将 PDES 预测结果与现有监测指标（如 ARG 丰度）关联有何建议？
  - 我们如何设计实验来验证 PDES 的预测，同时兼顾成本和可行性？

## 2. 西北农林科技大学罗自卫老师

- Source: `20260320_罗自卫老师湿实验访谈_HP小循环_JU_Krakow风格_中文版修改.docx`
- Status: `L3_Evidenced`
- Priority: `0.843`
- Categories: Safety, Model, Software, Implementation, Material
- Next step: 根据罗老师建议，调整湿实验路线并筛选7条候选肽，同时完善证据链和软件标签，建议回访时展示初步MIC和安全性数据，并讨论表达系统选择。
- Materials: 更新后的湿实验路线图（含化学合成、MIC、溶血/CCK-8、TEM、表达纯化）, 7条候选肽的序列及筛选依据说明, 软件报告中Evidence Level和Production Feasibility标签的示例, 初步MIC或安全性数据（如有）
- Suggested questions:
  - 您认为在表达纯化阶段，大肠杆菌、毕赤酵母和枯草芽孢杆菌哪个更适合我们目前的候选肽？
  - 对于短肽在胶上难以观察的问题，您建议优先采用哪种检测方法（如WB、液相或质谱）？
  - 在后续实验中，如何更场景化地验证羊乳腺细胞的安全性？是否需要引入原代细胞或3D模型？
  - 您对7条候选肽的数量和筛选依据有何进一步建议？

## 3. 西北农林科技大学家畜生物学重点实验室刘军教授

- Source: `20260309_家畜生物学重点实验室调研_HP小循环_JU_Krakow风格_中文版.docx`
- Status: `L3_Evidenced`
- Priority: `0.83`
- Categories: Safety, Model, Implementation, Problem Definition, Software
- Next step: 建议在完成体外筛选和模型评估后，向刘军教授反馈候选肽的MIC、溶血和细胞毒性数据，并讨论在羊群中进行初步现场验证的可行性。
- Materials: 候选抗菌肽的体外活性与毒性数据汇总表, AMPlify 项目更新版海报或幻灯片, 关于乳腺炎场景适配的模型预测报告
- Suggested questions:
  - 您认为我们目前的候选肽在哪些理化性质上还需要优化，以更好地适应乳汁环境？
  - 对于隐性乳腺炎的检测，您有哪些建议可以帮助我们在现场评估中更准确地判断疗效？
  - 在羊群中进行初步试验时，您认为最关键的伦理和操作注意事项是什么？

## 4. 赵天意老师，生物大数据相关方向教师

- Source: `20260315_赵天意老师访谈_HP技术小循环_主线优化版_JU_Krakow风格_中文版.docx`
- Status: `L3_Evidenced`
- Priority: `0.824`
- Categories: Safety, Model, Implementation, Material, Problem Definition
- Next step: 建议在完成一轮合成与活性验证后，带着实测数据回访赵老师，重点展示判别器与生成器的协同效果，并请教如何进一步优化筛选阈值。
- Materials: TAM-Flow 模型架构与训练流程说明, 初步合成肽的 MIC、溶血及细胞毒性数据, 与随机序列对比的理化性质分布图
- Suggested questions:
  - 您认为当前判别器的评分权重是否合理？哪些指标应优先考虑？
  - 对于少量合成候选的高失败风险，您建议如何扩大候选多样性或提高命中率？
  - 在膜相互作用分析中，哪些实验或模拟手段最能有效筛选抗菌肽？

## 5. 武功县诚威奶山羊羊场负责人杜欣愿

- Source: `20260422_武功县诚威奶山羊羊场负责人杜欣愿羊乳房炎调研_HP利益相关者主线_JU_Krakow风格_中文版，修改.docx`
- Status: `L3_Evidenced`
- Priority: `0.787`
- Categories: Implementation, Problem Definition, Safety, Material, Model
- Next step: 建议团队在下一轮回访中，携带基于广谱候选肽的体外抑菌数据（针对金葡菌和厌氧菌），并与养殖户讨论在真实羊场环境中进行小规模验证的可行性，同时收集关于给药方式和疗程的进一步反馈。
- Materials: 候选抗菌肽的体外抑菌谱数据（含金葡菌和厌氧菌）, 广谱抗菌肽与传统抗生素的对比说明图, 羊场乳房炎病例记录表模板
- Suggested questions:
  - 如果我们的候选肽在体外对金葡菌和厌氧菌都有效，您是否愿意参与后续的小规模羊场试验？
  - 您认为在实际治疗中，注射和灌注哪种方式更容易操作？对肽类药物的剂型有什么期望？
  - 对于慢性复发性乳房炎，您希望新疗法在疗程和费用上达到什么水平才愿意替代现有抗生素？

## 6. 西北农林科技大学西安动物医院临床医生、院长及检验中心工作人员

- Source: `20260124_西安动物医院调研_HP小循环_JU_Krakow风格_中文版.docx`
- Status: `L3_Evidenced`
- Priority: `0.765`
- Categories: Problem Definition, Safety, Model, Implementation, Software
- Next step: 针对兽医临床反馈，建议在后续调研中优先收集畜禽、泌乳期和蛋鸡养殖端的减抗需求与残留控制数据，并完善抗菌肽候选物的局部给药路径与证据等级评估。
- Materials: AMPlify候选肽的体外活性与安全性数据摘要, 皮肤/耳道局部感染场景的案例或文献资料, 畜禽减抗政策与残留标准的相关文件
- Suggested questions:
  - 在畜禽养殖中，哪些具体感染场景对抗菌肽的局部或口服应用需求最迫切？
  - 针对泌乳期和蛋鸡，残留控制对抗菌肽开发有哪些特殊要求？
  - 您认为抗菌肽作为辅助或保健产品，在宠物临床中的定位应如何与现有抗生素策略互补？

## 7. 基层执业兽医与散养户（乡村散养羊户）

- Source: `20260501_下乡采访散养羊村民_HP利益相关者主线_JU_Krakow风格_中文版.docx`
- Status: `L3_Evidenced`
- Priority: `0.726`
- Categories: Problem Definition, Safety, Implementation, Environment, Education
- Next step: 回访时用更朴实的语言解释抗菌肽的定位，强调其是疫苗和管理的补充而非替代，并展示体外实验数据说明验证边界。
- Materials: 抗菌肽作用机制的通俗图解, 体外实验数据摘要（非临床）, 疫苗与抗菌肽互补关系的说明单页
- Suggested questions:
  - 您觉得我们这样解释抗菌肽，是否更容易理解？
  - 在您的养殖实践中，哪些环节最需要抗菌肽这类工具？
  - 您认为我们还需要提供哪些证据，才能让您更信任这个方案？

## 8. 哈尔滨工业大学生命科学与医学学部聂桓老师

- Source: `20260418_哈工大生命学院院长调研_HP简版_JU_Krakow风格_中文版修改.docx`
- Status: `L3_Evidenced`
- Priority: `0.71`
- Categories: Education, Model, Implementation, Problem Definition, Software
- Next step: 建议在后续回访中，向聂桓老师展示项目在跨学科叙事和工程化目标上的具体改进，并探讨如何将共享失败经验与不可复制资源纳入合作框架。
- Materials: 更新后的项目介绍PPT（突出工程化目标与证据边界）, 跨学科合作框架草案（含共享失败经验与不可复制资源的机制）, 项目Wiki页面截图（展示叙事改进）
- Suggested questions:
  - 您认为我们在项目介绍中如何更清晰地表达工程化目标，以便其他团队快速理解？
  - 对于共享失败经验，您建议我们采用哪些具体形式或平台？
  - 您觉得哪些类型的不可复制资源最值得在跨校合作中共享？
  - 我们的叙事改进是否有效解决了您之前提到的‘被看懂’问题？

## 9. 杨陵揉谷镇除张村羊场人员张伟

- Source: `20260420_杨陵除张村羊场人员张伟调研_HP利益相关者主线_JU_Krakow风格_中文版.docx`
- Status: `L2_Actioned`
- Priority: `0.689`
- Categories: Implementation, Problem Definition, Safety, Material, Environment
- Next step: 回访时请携带广谱型候选肽的体外活性与安全性数据，并演示拌料给药方案的成本估算，重点说明对羊奶质量无影响。
- Materials: 广谱型候选抗菌肽的体外活性与安全性数据摘要, 拌料给药方案的成本估算与操作流程说明, 羊奶质量影响评估的初步结果（如有）
- Suggested questions:
  - 您对拌料给药方式的具体操作细节和成本接受度如何？
  - 在混合感染场景下，您希望抗菌肽对哪些病原菌有优先覆盖？
  - 如果抗菌肽能降低乳房炎发病率，您愿意为此增加多少成本？

## 10. 西安市浮生闲猫咪驿站工作人员

- Source: `20260419_西安市浮生闲猫咪驿站工作人员调研_HP利益相关者主线_JU_Krakow风格_中文版.docx`
- Status: `L2_Actioned`
- Priority: `0.637`
- Categories: Problem Definition, Education, Safety, Implementation, Environment
- Next step: 建议在后续回访中，向驿站工作人员展示 AMPlify 在宠物皮肤病与局部感染场景的体外评估数据，并共同探讨如何将'诊断-剂量-联合用药'认知融入项目教育材料，同时明确项目当前仅处于科研阶段，不涉及临床使用。
- Materials: AMPlify 宠物皮肤感染场景的体外评估结果摘要, 抗菌肽与传统抗生素作用机制对比的科普折页, 宠物用药认知调查问卷（用于收集更多反馈）
- Suggested questions:
  - 您认为在宠物皮肤病治疗中，主人最常出现的用药误区有哪些？
  - 如果 AMPlify 未来提供辅助诊断建议，您希望它以什么形式呈现给宠物主人？
  - 您觉得哪些信息最能帮助宠物主人理解抗菌肽替代方案的科研边界？

## 11. 吉林大学举办的iGEM东北地区交流会参会队伍、经验分享者及其他iGEM成员

- Source: `20260502_iGEM东北地区交流会_HP主线校准_JU_Krakow风格_中文版(1).docx`
- Status: `L2_Actioned`
- Priority: `0.602`
- Categories: Education, Implementation, Problem Definition, Environment, Social Media
- Next step: 建议在后续交流会上向分享者展示更新后的Wiki主线与HP叙事，并请其评估逻辑一致性是否提升。
- Materials: 更新后的Wiki概述页与摘要卡片, HP故事主线图（Stakeholder→Feedback→Action→Impact）, Education互动活动记录与反馈, 调研与项目修改对照表
- Suggested questions:
  - 您认为我们现在的HP叙事是否清晰体现了每个反馈如何转化为行动？
  - 在Education方面，我们调整后的互动活动是否更有效地让受众理解问题？
  - Wiki、海报和答辩的逻辑一致性是否还有改进空间？
  - 您对我们下一步的HP重点有何建议？
