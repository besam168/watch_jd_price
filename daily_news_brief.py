import argparse
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

SENDER = '910633260@qq.com'
AUTH_CODE = 'sghqeeeeyuzjbcbb'
RECEIVERS = ['besam168168@gmail.com', '758622673@qq.com']
SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 465


def build_comprehensive_brief(now: datetime.datetime) -> tuple[str, str]:
    cn_date = now.strftime('%Y年%m月%d日')
    subject = f'【沈万三】每日新闻小报告 - 综合版 - {cn_date}'
    body = f"""# 每日新闻小报告（综合版）

**日期：** {cn_date}
**时间：** {now.strftime('%Y-%m-%d %H:%M:%S')}
**整理：** 沈万三 💰

---

## 一、今日重点（简版）
- 全球市场：重点关注美股、亚太股市、原油、黄金与美元波动。
- 地缘政治：重点关注中东、俄乌、中美关系的最新进展。
- 宏观经济：重点观察通胀、利率、央行动向与就业数据。

## 二、看盘框架
- **先看风险资产：** 美股三大指数、纳指科技权重。
- **再看避险资产：** 黄金、美债、美元指数。
- **再看商品：** 原油、铜、天然气等是否出现趋势变化。

## 三、今日行动建议
- 没有明确增量信息前，先看方向，不重仓乱动。
- 若市场波动加剧，优先保留现金与流动性。
- 若出现重大国际突发事件，优先检查原油、黄金与指数期货。

## 四、结论
这版改为**小报告机制**，目标是每天快速给出一份能看、能用、能迅速扫完的简报，替代原来偏长的自动模板。

---

**说明：** 这是新的轻量日报模板，用于替代原先的长篇自动定时任务内容。
"""
    return subject, body


def build_tech_brief(now: datetime.datetime) -> tuple[str, str]:
    cn_date = now.strftime('%Y年%m月%d日')
    subject = f'【沈万三】每日新闻小报告 - 科技版 - {cn_date}'
    body = f"""# 每日新闻小报告（科技版）

**日期：** {cn_date}
**时间：** {now.strftime('%Y-%m-%d %H:%M:%S')}
**整理：** 沈万三 💰

---

## 一、今日科技观察
- AI：继续关注大模型、Agent、多模态、AI 硬件。
- 消费电子：关注 Apple、Samsung、PC、手机、AR/VR。
- 机器人：关注自动驾驶、仓储机器人、具身智能。

## 二、今天重点看什么
- **产品发布：** 是否有大厂新模型、新设备、新系统。
- **资本动作：** 是否有大额融资、并购、合作。
- **产业趋势：** 是否有值得长期跟踪的新方向。

## 三、行动建议
- 短期先抓“重要发布 + 产业趋势”，不要堆太多碎新闻。
- 只保留真正值得看的 3-5 条，不做大而全堆料。
- 如无重大更新，可以明确写“今日无重大更新”。

## 四、结论
科技版也切到**小报告机制**：更轻、更快、更适合每天扫一遍，替代原来较长的自动科技报告模板。

---

**说明：** 这是新的轻量科技日报模板，用于替代原先的长篇自动定时任务内容。
"""
    return subject, body


def send_email(subject: str, body: str) -> bool:
    msg = MIMEMultipart()
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECEIVERS)
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        smtp.login(SENDER, AUTH_CODE)
        smtp.sendmail(SENDER, RECEIVERS, msg.as_string())
        smtp.quit()
        print(f'Email sent successfully: {subject}')
        return True
    except Exception as e:
        print(f'Email sending failed: {e}')
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description='发送每日新闻小报告')
    parser.add_argument('--mode', choices=['comprehensive', 'tech'], required=True)
    args = parser.parse_args()

    now = datetime.datetime.now()
    if args.mode == 'comprehensive':
        subject, body = build_comprehensive_brief(now)
    else:
        subject, body = build_tech_brief(now)

    success = send_email(subject, body)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
