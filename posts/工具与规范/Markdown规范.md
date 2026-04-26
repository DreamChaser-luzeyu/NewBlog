---
date: 2026-04-26
tags:
- Markdown
- 写作规范
- Pandoc
- LaTeX
title: Markdown规范
---

# Markdown规范

**请勿再编辑此文档，请去模板仓库修改`README.md`**

- 开头定义这些关键字，模板不一定支持全部这些关键字

  ```markdown
  ---
  doctype: 文档类型
  title: 文章标题
  entitle: 英文标题
  rhead: 页眉标题（右）
  author: 作者
  tutor: 指导教师
  major: 专业
  grade: 年级
  keywords: 关键词一\ 关键词二\ 关键词三
  keywords_en: key1 key2 key3
  abstract: 摘要内容特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字特别多字
  abstract_en: abstract content many words many words many words many words many words many words many words many words many words many words many words
  ---
  ```

  
- 不允许使用Typora的图片缩放（因为这个功能会把图片变成HTML标签，pandoc就不会识别）
- 使用`\cite{desc}`来引用参考文献

- draw.io画的`.svg`必须以`.drawio.svg`为后缀

- Markdown中插入图片可以用这种格式，这样可以以latex的方式引用

  - ```markdown
    ![caption_desc \label{label_desc}](path/to/pic)
    ```

- ~~行内公式在LaTeX PDF中无法正常显示，使用公式块（两个"$"包裹）。~~