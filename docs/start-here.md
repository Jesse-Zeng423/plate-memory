# A seat saved for you / 给你留了个座

You can be hungry first. Everything else is optional.

## Start / 启动

This is the v1.0.0 local release. Requires Python 3.10+. Download and unzip the
[release package](https://github.com/Jesse-Zeng423/plate-memory/releases/latest), then open its folder in Terminal:

```sh
python3 plate-memory.py
```

On macOS you can also double-click `start.command`; if permissions block it, use
the Python command above. On macOS/Linux, `sh start.sh` works too. `--version`
shows the installed version. Normal mode uses your own empty local records; it
does not load the synthetic profile. Confirmed data stays in `private/` next to the
app. Keep that folder when moving or replacing the app; back it up privately.

Choose **1 English** (Enter is enough) or **2 简体中文**. Try **1 Find something to eat**:
too tired → takeout; up for a walk → cafeteria. Enter a food name, or press Enter
to browse. Pick a shown number, then **1 Pick**. Nothing is ordered or logged.
The app suggests reference foods; check your actual menu for price and ingredients.

启动后选语言，再选 **1 找点好吃的**：太累了看外卖，可以走走就去食堂。
输入三明治、汤、酸奶等，或回车随便看看。选编号，再选 **1 就选这个**。
工具只帮你想吃什么，不会下单。当天供应、价格和配料请核对真实菜单。

No account, API key, model download or dietary profile is needed for this path.
The separate `--demo` mode has clearly synthetic places, prices and dietary notes.
Demo changes disappear when you close the app.

这条流程无需账号、API key、模型下载或填写饮食资料。`--demo` 是标注清楚的
合成演示，不是 Harold 的真实偏好；关闭后不保留修改。

## Return / 返回

- Action menus: **0 Back**, **h Home**. You can also type `/back` or `/home`.
- Form fields: `/back` edits the previous answer; `/home` keeps a session draft.
- `/skip` clears an optional field; Enter keeps a shown default.
- `/cancel` asks before discarding a draft. Closing the app discards unsaved drafts.

菜单里的 **0 返回**、**h 饭桌**一直可用。填写时 `/back` 回上一项，`/home`
回饭桌并暂留草稿，`/skip` 清空可选项，`/cancel` 确认后丢弃草稿。
草稿不写到磁盘，关闭应用后就没有了。

## A note from a friend / 朋友的小饭盒

Choose **2 Lunchbox → 1 Open file**, paste the path of a received `lunchbox.json`,
preview it, then choose yes to keep it locally. A postcard HTML/PNG is for viewing;
`lunchbox.json` is the file to import. You can write your own note with **2 Write**.

选 **2 朋友的小饭盒 → 1 打开文件**，粘贴收到的 `lunchbox.json` 路径，预览后
确认保存。HTML/PNG 明信片用来欣赏，饭盒 JSON 用来导入。也可以选 **2 写饭盒**。

## Send a postcard yourself / 亲自分享明信片

Choose **4 Postcard**, write names and a note. **3 Style** offers a cafeteria table,
a takeout receipt or a lunch invitation. Export a share folder (HTML, text, lunchbox
JSON), or an individual file. Only fields shown in preview are shared. Include the
public project quick-start link if you want your friend to try the tool.

选 **4 下次，再一起吃**，写名字和留言。**3 样式**可选食堂桌边、外卖小票、
下次饭约。可以导出分享文件夹，或单个文件；确认加入使用链接后，朋友可找到
启动说明。没有自动发送，也不会附带日记、饮食记录或个人资料。

HTML opens in a browser without internet. PNG optionally uses an installed local
Chrome/Chromium in an isolated temporary profile. If PNG fails, choose HTML; the
note is kept. Older share folders are never overwritten. Existing individual files
require explicit replacement confirmation. Files are local and owner-only on POSIX,
not encrypted. Exports remain until you delete them yourself.

## Local AI / 本地 AI

Browsing works immediately. For describing a craving or checking dietary notes
against a pasted menu with local Gemma, follow the [README setup](../README.md#run-the-real-local-ai).
Model output only extracts candidates. Python rules decide whether a remembered
note can apply. No cloud inference or API keys. Allergy/cross-contact verification
still requires the preparer. No restaurant search, health score or delivery ordering.


## A rough craving is enough

Try `something warm` or `I want noodles`. A recognized direction offers nearby
food ideas; pick a number for its family and menu checklist, or **4 Similar ideas**.
These are references to look for, not live shops, prices or nutritional rankings.
`n` more · `p` previous · `c` families · `a` save a place · `d` local AI description.

Demo postcards can now be exported too: **4 → write → 1 Export → choose format**.
The note is saved only at the chosen path; demo meal/profile records stay in memory.
