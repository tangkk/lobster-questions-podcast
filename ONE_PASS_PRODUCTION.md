# 龙虾问题 · One-pass Production SOP

## 栏目定位

每一期从一个真实问题出发，不限哲学、经济、心理、科学或技术；不以介绍知识点为目的，而是把问题多想几层。

## Canonical 原则

`episodes/*.txt` 是唯一口播正文。Preview、正式 Podcast 与文字版正文必须来自同一 canonical；Preview 之后如修改 canonical，必须重新生成 Preview。

## 标准流程

1. 在独立分支新增或修改一个 `episodes/*.txt`，提交 PR。
2. `TTS Preview` 只生成试听 artifact，不更新 RSS、不上传正式音频。
3. Preview 成功后通知。
4. 用户要求“发来听一下”时：发送该 Preview；同时发布文字版，正文逐字对应 canonical，并在文章顶部嵌入当前 Preview 音频。Preview 音频必须放在 R2 `questions/preview/` 路径，与正式 Podcast 隔离。
5. 用户明确说“发布”后，使用刚刚试听并批准的同一个 artifact；禁止重新 TTS。
6. 发布前校验 MP3 SHA256、真实字节数和 ffprobe 时长；正式音频上传 `questions/epNNN-*.mp3`，RSS `enclosure length` 与 `itunes:duration` 必须使用实测值。
7. 正式发布完成后，文字页可以只把播放器从 Preview URL 切到正式 URL，正文不得变化。

## 失败策略

任何一步失败都先定位失败点，不盲目重跑完整链路。重复请求必须通过 GUID、R2 object existence 和 SHA 校验避免二次发布。

## 文字版成功标准

源码提交不等于发布成功。必须同时验证：Pages 部署成功、文章 URL 200、首页能看到文章、正文与 canonical 一致、播放器 URL 存在且可访问。
