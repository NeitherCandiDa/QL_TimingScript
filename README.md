# 工作繁忙，有缘更新！！！

访问量![Visitor Count](https://profile-counter.glitch.me/NeitherCandiDa-QL_TimingScript/count.svg)

# 青龙拉取

订阅管理->创建订阅->保存
> 拉取链接：https://gitee.com/liu-long068/QL_TimingScript.git

![输入图片说明](.idea/inspectionProfiles/image.png)

# 安装依赖

依赖管理->Python3->创建依赖

![输入图片说明](.idea/inspectionProfiles/image2.png)

# 已完成

|                  |                                      | 是否可用 |
|:-----------------|:------------------------------------:|:--------:|
| 微信每日早安推送 | WeChatPublicNumberPushInformation.py |    ✅    |
| 品赞代理         |             pzSignIn.py              |    ✅    |
| 好游快爆         |      好游快爆浇水爆米花任务.py       |    ❌    |
| 哈啰             |           hello_signIn.py            |    ❌    |
| 中国移动云盘（AI豆） |        中国移动云盘-新版.py         |    ✅    |
| 得物森林         |             得物森林.py              |    ✅    |
| 滴滴出行         |             滴滴出行.py              |    ❌    |
| 同程旅行         |               tclx.py                |    ❌    |
| 浓五的酒馆       |            浓五的酒馆.py             |    ❌    |
| 顺丰速运         |               sfsy.py                |    ❌    |
| OPPO商城         |             OPPO商城.py              |    ❌    |
| 安慕希           |              anmusi.py               |    ❌    |

## 中国移动云盘（AI豆）脚本变量

`中国移动云盘-新版.py` 用到的环境变量（脚本开头注释里有完整的「怎么获取」说明）：

| 变量                | 必需 | 说明                                                                     |
|:--------------------|:----:|:-------------------------------------------------------------------------|
| `ydyp_ck`           |  ✅  | `authorization#手机号[#jwtToken][#deviceId]`，多账号用 `@` 分隔           |
| `ydyp_ua`           | 建议 | 自己手机的 User-Agent（抓包复制整串）。不填用内置机型，多人同一串易被风控 |
| `ydyp_device_id`    | 可选 | 默认设备号；不填按账号派生一个稳定 UUID，各人互不相同                      |
| `ydyp_device_token` | 建议 | 真机设备令牌；**不填则签到/领记录豆被回 614**，抓一次可长期用（见下）       |
| `ydyp_upload_fill`  | 可选 | 是否补足「当月上传满 100 个」，默认 `0`（该通道实测不计入计数）            |

device token 怎么拿（关键）：抓包工具里搜 `receiveV3`（或搜你待领记录的那串数字 ID），
打开那条 POST，复制**请求体里的 `deviceId` 整串**（约 88 字符 base64，形如
`AbCdEf012345...Q==`）填进 `ydyp_device_token`。它由 App 内置 SMSdk 依设备指纹生成、
本机固定，抓一次可长期用；不填的话签到与领记录豆会被服务端判为未知设备，一律回 614。

authorization 怎么拿：手机装 Reqable 抓 App 任意请求的请求头，或用本仓库自带的
「移动云盘抓authorization.zip」（解压后管理员运行，自动抓出）。有效期约 30 天，
接口返回 `05050006 暂无权限！` 即过期，重抓一次替换即可。

配置完先跑只读自检（不签到、不领豆，只打印凭据/豆余额/任务/活动状态）：

```
python 中国移动云盘-新版.py --check
```

# 其他

脚本的变量设置，以WeChatPublicNumberPushInformation.py为例：
> 环境变量->创建变量 变量名以脚本内要求为准

![输入图片说明](.idea/inspectionProfiles/image3.png)

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=NeitherCandiDa/QL_TimingScript&type=Date)](https://www.star-history.com/#NeitherCandiDa/QL_TimingScript&Date)

# 特别声明

本仓库发布的脚本及其中涉及的任何解锁和解密分析脚本，仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断。

本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。

本人对任何脚本问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害。

间接使用脚本的任何用户，包括但不限于建立VPS或在某些行为违反国家/地区法律或相关法规的情况下进行传播, 本人对于由此引起的任何隐私泄漏或其他后果概不负责。

请勿将本仓库的任何内容用于商业或非法目的，否则后果自负。

如果任何单位或个人认为该项目的脚本可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关脚本。

任何以任何方式查看此项目的人或直接或间接使用该项目的任何脚本的使用者都应仔细阅读此声明。本人保留随时更改或补充此免责声明的权利。一旦使用并复制了任何相关脚本或Script项目的规则，则视为您已接受此免责声明。

您必须在下载后的24小时内从计算机或手机中完全删除以上内容

您使用或者复制了本仓库且本人制作的任何脚本，则视为 已接受 此声明，请仔细阅读
