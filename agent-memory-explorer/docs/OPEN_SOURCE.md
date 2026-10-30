# 首轮开源核查 · 2026-10-30

范围：A-MEM动态关联机制与3D渲染组件。状态分为网页文档核查、固定版本源码核查、本地运行；本次仅前者取得部分结果。

## 访问失败记录

Python直接访问GitHub API：WujiangXu/A-mem超时；vasturiano/3d-force-graph HTTP 403。原始结果保留于 research.json。不能据此断言项目不可用。

## 网页核查结果

- https://github.com/agiresearch/A-mem ：系统库，README声明MIT。含结构化笔记、ChromaDB关联、记忆更新；论文复现指向另一个仓库 https://github.com/WujiangXu/AgenticMemory 。拟研究局部召回与提案生成，不直接采用其存储作权威。未检查源码提交及删除/人工保护语义，暂不引入依赖。
- https://github.com/vasturiano/3d-force-graph ：README与仓库声明MIT；Three.js/WebGL，支持三维力导向。官方示例包含自定义节点、节点聚焦、展开收起、拖动固定和Bloom。优先验证作为正式3D适配器；布局计算输出仅可写布局版本，不可改内容或组织关系。
- https://github.com/vasturiano/three-forcegraph ：MIT标识，提供Three.js场景对象，比完整组件更底层；作为需要更深星云材质定制时的备选。
- https://github.com/moonskorch/ReverySky-Plugin ：检索发现但官方页面读取失败，未核实许可证及实现，不作复用依据。

固定提交：尚未取得。安装与本地运行：未执行。实际复用代码：无。正式选型前必须补齐提交、许可证文件、依赖锁定和真实接口交互实验；网页功能声明不是本项目运行证据。
