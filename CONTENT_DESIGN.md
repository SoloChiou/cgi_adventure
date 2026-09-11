# CGI Adventure 內容設計總表

> 文件狀態：Draft v0.1
> 目的：記錄中國鬼怪文學題材的內容關係、來源依據與改編決策。遊戲規則與內容範圍以 `PROJECT_SPEC.md` 為準；實際可執行數值以 `seed_game` 為準。

## 1. 文件分工

```text
內容資料分工
├─ PROJECT_SPEC.md
│  └─ 世界觀方向、內容範圍、遊戲規則與資料契約
│
├─ CONTENT_DESIGN.md
│  └─ 場地、人物、怪物、物品、職業與技能的關係及改編理由
│
├─ seed_game
│  └─ 可由 Git 追蹤且可重建的正式內容與遊戲數值
│
└─ Database
   └─ 遊戲執行時查詢的內容資料，不作為唯一來源
```

## 2. 文學來源定位

```text
中國鬼怪文學題材
├─ 《山海經》
│  └─ 上古地理、異獸、神祇、奇物與未知邊境
│
├─ 《聊齋志異》
│  └─ 城鎮、荒寺、書齋、狐鬼、人鬼相遇與世情
│
├─ 《西遊記》
│  └─ 洞府、妖王、道佛修行、法寶與神魔旅途
│
└─ 《封神演義》
   └─ 仙門、陣法、法寶、神將與封神體系
```

四部作品是主要內容來源，不代表彼此設定自然屬於同一正史。遊戲以分區、章節和內容來源維持脈絡，再以原創世界框架連接。引用原典名稱時需保存具體出處；融合、簡化或重新賦予能力時標示為改編；僅借用志怪氣氛者標示為原創。

## 3. 來源欄位

```text
內容來源資料
├─ source_work
│  └─ 來源作品；純原創內容可留白
│
├─ source_reference
│  └─ 篇章、人物、異獸、器物出處或可辨識的設計依據
│
├─ adaptation_type
│  ├─ canonical：名稱與核心身分直接取自原典
│  ├─ adapted：融合、簡化或遊戲化改編
│  └─ original：遊戲原創內容
│
└─ lore_note
   └─ 內部考據、改編範圍及避免誤解的說明，不預設顯示給玩家
```

目前欄位適用於 `Area`、`Monster`、`Item` 與 `Job`。未來新增 NPC 或 Skill 內容模型時沿用相同契約；玩家建立的 `Player` 不屬於典籍內容，不使用這些欄位。

## 4. 已停止採用的第一個垂直切片

```text
蘭若古道（已取消）
├─ 場地
│  ├─ 來源：《聊齋志異》〈聶小倩〉的蘭若寺與志怪旅途意象
│  ├─ 類型：改編
│  └─ 定位：曾規劃為通往荒寺的初期戰鬥地區，目前停止採用且不再由 Seed 建立
│
├─ 初始職業
│  └─ 遊方客：原創的未轉職身分
│
├─ 怪物
│  ├─ 遊魂：原創普通怪物，採志怪文學常見亡魂意象
│  ├─ 狐魅：改編自《聊齋志異》多篇狐鬼故事的共同意象
│  └─ 畫皮鬼：改編自《聊齋志異》〈畫皮〉，作為初期精英怪物
│
└─ 物品
   ├─ 桃木劍：原創初始武器，採民間桃木辟邪意象
   ├─ 舊道袍：原創普通防具
   ├─ 狐紋古玉：依狐魅題材改編的稀有飾品
   └─ 陰氣殘縷：原創掉落材料
```

蘭若古道已取消。遊魂、狐魅、畫皮鬼、桃木劍、舊道袍、狐紋古玉與陰氣殘縷保留為候選內容，但不再建立蘭若古道或其遭遇關聯；未來必須在新地區內容定案後重新建立關係。

```text
已取消的本機驗證內容
└─ 等級模擬場
   ├─ 狀態：已取消，DEBUG 與 Production 均不再建立或提供入口
   ├─ 修行幻影：保留既有資料供歷史紀錄追溯，不再由 Seed 建立
   └─ 資料處理：既有地區停用；既有怪物與遭遇不再使用但不主動刪除
```

## 5. FF Adventure 型職業內容方向

FF Adventure 提供多職業、七種特性門檻與職業內七階稱號的結構參考；本專案不直接使用其日文職業名稱、必殺技名稱或 Final Fantasy 相關素材。正式內容以中國鬼怪文學與原創志怪框架重新命名，實際規則與數值仍須在 `PROJECT_SPEC.md` 逐項定案。

```text
十四職業正式架構方向
├─ 1. 武者
│  ├─ 結構參考：Fighter
│  ├─ 英文名稱：Warrior
│  ├─ 定位：力量導向的正面物理戰鬥
│  ├─ 代表技能：破邪斬｜Evil-Rending Slash
│  ├─ 武器：刀、劍、槍
│  └─ 類型：原創；採中國武人與遊俠意象
│
├─ 2. 方士
│  ├─ 結構參考：Mage
│  ├─ 英文名稱：Mystic
│  ├─ 定位：智識導向的符法與五行攻擊
│  ├─ 代表技能：五行符｜Five Elements Talisman
│  ├─ 武器：法劍、法杖、符器
│  └─ 類型：改編；採中國方術與志怪術士意象
│
├─ 3. 祝由師
│  ├─ 結構參考：Priest
│  ├─ 英文名稱：Ritual Healer
│  ├─ 定位：信念導向的治療、祓除與護持
│  ├─ 代表技能：祝由祓煞｜Ritual Banishment
│  ├─ 武器：法杖、符器
│  └─ 類型：改編；名稱取自傳統祝由意象，能力為遊戲化設計
│
├─ 4. 夜行客
│  ├─ 結構參考：Thief
│  ├─ 英文名稱：Night Rogue
│  ├─ 定位：靈巧、速度與奇襲
│  ├─ 代表技能：夜襲｜Night Assault
│  ├─ 武器：短刃、劍
│  └─ 類型：原創；採夜行與江湖奇人意象
│
├─ 5. 山林獵手
│  ├─ 結構參考：Ranger
│  ├─ 英文名稱：Wilds Hunter
│  ├─ 定位：均衡探索、遠程武器與妖物追蹤
│  ├─ 代表技能：伏妖箭｜Demon-Subduing Arrow
│  ├─ 武器：弓、弩、刀
│  └─ 類型：原創；採山野獵戶與志怪旅途意象
│
├─ 6. 丹師
│  ├─ 結構參考：Alchemist
│  ├─ 英文名稱：Alchemist
│  ├─ 定位：智識與靈巧導向的丹藥、器物與變化
│  ├─ 代表技能：丹火化形｜Elixir Flame Transmutation
│  ├─ 武器：法杖、符器
│  └─ 類型：改編；採煉丹與方術意象，不對應特定宗派
│
├─ 7. 樂師
│  ├─ 結構參考：Bard
│  ├─ 英文名稱：Minstrel
│  ├─ 定位：音律、魅力與輔助效果
│  ├─ 代表技能：清商鎮魂｜Pure Melody Soulward
│  ├─ 武器：樂器、短刃
│  └─ 類型：原創；採古代樂師與志怪音律意象
│
├─ 8. 通靈者
│  ├─ 結構參考：Psionic
│  ├─ 英文名稱：Spirit Medium
│  ├─ 定位：智識、生命與魅力導向的神念能力
│  ├─ 代表技能：通幽神念｜Netherworld Communion
│  ├─ 武器：法杖、符器
│  └─ 類型：原創；採感應鬼神與通幽意象
│
├─ 9. 神女
│  ├─ 結構參考：Valkyrie
│  ├─ 英文名稱：Divine Maiden
│  ├─ 定位：力量、信念、生命與速度兼具的戰鬥者
│  ├─ 代表技能：神女降魔｜Divine Demonfall
│  ├─ 武器：槍、劍
│  └─ 類型：原創；使用泛稱，不對應特定神祇或原典人物
│
├─ 10. 法主
│  ├─ 結構參考：Bishop
│  ├─ 英文名稱：Arcane Hierophant
│  ├─ 定位：高智識與高信念的術法領袖
│  ├─ 代表技能：萬法歸一｜Convergence of All Arts
│  ├─ 武器：法杖、法劍
│  └─ 類型：原創；避免對應現實宗教職位
│
├─ 11. 仙門宗主
│  ├─ 結構參考：Lord
│  ├─ 英文名稱：Immortal Sect Master
│  ├─ 定位：高門檻的全能領袖
│  ├─ 代表技能：仙門敕令｜Immortal Sect Edict
│  ├─ 武器：劍、法劍
│  └─ 類型：原創；採仙門與宗派領袖意象
│
├─ 12. 劍客
│  ├─ 結構參考：Samurai
│  ├─ 英文名稱：Swordmaster
│  ├─ 定位：力量、靈巧與速度導向的武器專家
│  ├─ 代表技能：御劍疾斬｜Swift Flying Sword
│  ├─ 武器：劍
│  └─ 類型：原創；改用中國劍俠意象，不沿用日本武士文化設定
│
├─ 13. 行者
│  ├─ 結構參考：Monk
│  ├─ 英文名稱：Ascetic
│  ├─ 定位：力量、信念與速度導向的徒手修行者
│  ├─ 代表技能：金剛伏魔｜Vajra Demon Subdual
│  ├─ 武器：拳套、棍
│  └─ 類型：原創；採雲遊修行者意象，不對應特定宗教人物
│
└─ 14. 影衛
   ├─ 結構參考：Ninja
   ├─ 英文名稱：Shadow Guard
   ├─ 定位：多能力門檻的高階隱密戰鬥者
   ├─ 代表技能：無影絕殺｜Shadowless Execution
   ├─ 武器：短刃、劍
   └─ 類型：原創；改用中國志怪與江湖中的影衛意象
```

```text
七種角色特性內容方向
├─ 膂力｜Strength：武器力量、負重與正面攻擊的角色素質
│
├─ 悟性｜Intelligence：術法理解、策略與法術威力的角色素質
│
├─ 信念｜Piety：祓除、護持、治療與精神抗性的角色素質
│
├─ 根骨｜Vitality：生命、耐力與承受傷害的角色素質
│
├─ 巧手｜Dexterity：武器控制、製作、命中與細緻操作的角色素質
│
├─ 身法｜Agility：行動順序、閃避與速度的角色素質
│
└─ 氣度｜Charisma：御靈、音律、交涉與領袖能力的角色素質
```

```text
職業內七階稱號
├─ 結構與作用
│  ├─ 等級區間依序為 Lv.1–6、7–13、14–20、21–27、28–34、35–41、42–99
│  ├─ 同一職業依角色等級顯示唯一稱號
│  ├─ 稱號不等同於轉職，不另外重設角色狀態
│  └─ 第一版只用於角色資料與排行榜顯示，不提供解鎖或能力效果
│
├─ 武者／Warrior
│  └─ 習武人／Martial Initiate → 持刃士／Blade Bearer → 破陣武士／Linebreaker → 鎮關豪傑／Pass Warden → 伏妖戰將／Demonbane General → 百戰宗師／Master of a Hundred Battles → 蕩魔武聖／Demon-Quelling War Saint
│
├─ 方士／Mystic
│  └─ 習符童／Talisman Novice → 行法士／Rite Adept → 五行術者／Fivefold Caster → 役鬼方士／Spirit Binder → 玄壇法師／Arcane Altar Master → 通天真人／Heaven-Reaching Sage → 乾坤道宗／Sovereign of Heaven and Earth
│
├─ 祝由師／Ritual Healer
│  └─ 習祝者／Ritual Novice → 安魂使／Soul Soother → 禳災師／Calamity Averter → 護命祝官／Life-Warding Ritualist → 百病祓師／Master of Banishment → 回春聖手／Sage of Renewal → 濟世祝宗／Grand Ritual Healer
│
├─ 夜行客／Night Rogue
│  └─ 探夜人／Night Scout → 潛蹤客／Veiled Strider → 飛簷手／Rooftop Runner → 無聲刺客／Silent Assassin → 逐影豪俠／Shadow Chaser → 幽都夜使／Nocturne Envoy → 萬影魁首／Sovereign of Shadows
│
├─ 山林獵手／Wilds Hunter
│  └─ 尋跡人／Trail Seeker → 山徑斥候／Mountain Scout → 伏妖弓手／Demonstalker Archer → 百獸獵師／Beastwise Hunter → 荒野巡狩／Warden of the Wilds → 群山守望／Sentinel of the Peaks → 萬嶺獵宗／Master of Ten Thousand Ridges
│
├─ 丹師／Alchemist
│  └─ 採藥童／Herb Gatherer → 煉火徒／Crucible Adept → 調鼎師／Cauldron Crafter → 百草丹師／Elixir Herbalist → 玄爐妙手／Mystic Crucible Master → 九轉丹宗／Master of Ninefold Elixirs → 造化藥君／Lord of Transmutation
│
├─ 樂師／Minstrel
│  └─ 習律人／Melody Novice → 清音客／Pure-Tone Minstrel → 鎮魂樂師／Soulward Musician → 幽弦妙手／Master of Phantom Strings → 百曲宗匠／Virtuoso of a Hundred Songs → 天籟樂聖／Sage of Celestial Harmony → 萬靈知音／Voice of All Spirits
│
├─ 通靈者／Spirit Medium
│  └─ 感靈人／Spirit Sensitive → 問魂使／Soul Inquirer → 通幽客／Netherworld Seer → 御念師／Mindweaver → 萬象靈媒／Medium of Myriad Forms → 陰陽先知／Oracle Between Realms → 太虛通靈聖／Sage of the Great Void
│
├─ 神女／Divine Maiden
│  └─ 奉燈女／Lamp Bearer → 護祠使／Shrine Warden → 玄甲神女／Mystic-Armed Maiden → 逐邪戰姬／Bane-Chasing Champion → 天門女將／General of the Heavenly Gate → 九霄英靈／Heroine of the Nine Heavens → 鎮世神姬／World-Warding Divine Maiden
│
├─ 法主／Arcane Hierophant
│  └─ 研法者／Arcane Scholar → 講法師／Doctrine Keeper → 掌壇使／Altar Custodian → 統法尊者／Exalted Arcanist → 萬法宗師／Master of Myriad Arts → 天章法主／Hierophant of the Celestial Canon → 玄穹聖宗／Sovereign of the Mystic Firmament
│
├─ 仙門宗主／Immortal Sect Master
│  └─ 外門執事／Outer Court Steward → 內門護法／Inner Court Guardian → 傳功長老／Teaching Hall Elder → 一峰之主／Master of One Peak → 仙門掌教／Head of the Immortal Sect → 群仙盟主／Lord of the Immortal Alliance → 萬宗共主／Sovereign of Ten Thousand Sects
│
├─ 劍客／Swordmaster
│  └─ 試劍人／Sword Aspirant → 行劍客／Wandering Swordsman → 疾風劍士／Gale Swordsman → 御劍名家／Flying Sword Adept → 斬妖劍豪／Demon-Slaying Swordmaster → 凌霄劍宗／Sky-Piercing Sword Sage → 一劍天尊／Celestial Sword Sovereign
│
├─ 行者／Ascetic
│  └─ 苦行人／Wayfaring Ascetic → 鍛體者／Body-Tempering Adept → 伏魔行者／Demon-Subduing Pilgrim → 金身護法／Golden-Body Guardian → 無畏尊者／Fearless Venerable → 明心大師／Master of the Clear Mind → 渡世聖行／World-Crossing Sage
│
└─ 影衛／Shadow Guard
   └─ 候影人／Shadow Watcher → 潛行衛／Veiled Guard → 無聲刃／Silent Blade → 夜幕使／Envoy of Night → 千面影衛／Thousand-Faced Guard → 無形統領／Commander Unseen → 幽影至尊／Sovereign of Hidden Shadows
```

上述十四個職業與九十八個稱號的繁體中文及英文名稱已確定為正式內容。七階結構參考 FF Adventure，但所有稱號均依中國志怪與武俠題材原創，不直接複製其 Class Title、日文內容、原始文字或素材。規則以 `PROJECT_SPEC.md` 為準並由 `seed_game` 保存。

```text
平行職業轉換設計
├─ 結構來源
│  ├─ 參考 FF Adventure 依目前特性開放其他職業的平行轉職架構
│  └─ 不沿用原始程式、文字、數值公式或素材
│
├─ 角色敘事
│  ├─ 轉職代表角色捨棄目前修行路線並從新道路重新入門
│  ├─ Lv.1、EXP 0 與初始特性表現重新打底，而非角色死亡或資料清除
│  └─ Gold、物品、經歷與武器熟練度保留，代表旅途成果仍屬於同一角色
│
└─ 十四職業
   ├─ 所有正式職業地位平行，不再區分三階進階關係
   ├─ 轉職前累積的特性決定當下可選道路
   └─ 轉職後特性回到新職業初始值，使下一次轉職必須重新成長
```

## 6. 已停用三階職業歷史

本節只記錄第 3 項導入前的職業內容與遷移依據，不再是 Runtime 正式內容。十四職業完成資料遷移後，舊職業只保留停用資料供歷史追溯；本節於第 13 項清理舊規格時移除。

```text
三階職業配置
├─ 近戰系
│  ├─ 金剛力士
│  │  ├─ 第一階：金剛力士；重裝近戰；改編自中國佛教文化中的金剛力士意象，不對應特定原典人物
│  │  ├─ 第二階：護法金剛；改編自護法與金剛意象，不對應特定原典人物
│  │  └─ 第三階：鎮獄神將；原創的鎮守幽冥神將稱號，不對應特定神祇
│  │
│  └─ 飛燕劍客
│     ├─ 第一階：飛燕劍客；敏捷近戰；原創，結合飛燕般的輕捷意象與中國武俠劍客形象
│     ├─ 第二階：流雲劍俠；原創，以行雲身法與劍俠意象延伸
│     └─ 第三階：凌霄劍仙；原創，以登臨雲霄的仙俠劍術意象延伸
│
├─ 召喚系
│  └─ 御靈師
│     ├─ 第一階：御靈師；召喚；原創，以駕馭靈體的中國志怪意象建立，不宣稱為歷史上的固定職業
│     ├─ 第二階：通幽使；原創，以通達幽冥並役使靈體的志怪意象延伸
│     └─ 第三階：萬靈宗師；原創，以統御多種靈體的最高階職業意象延伸
│
└─ 法術系
   └─ 方士
      ├─ 第一階：方士；法術；改編自中國方術與術士意象，不對應特定原典人物
      ├─ 第二階：五行術士；改編自陰陽五行與術士意象，不對應特定原典人物
      └─ 第三階：乾坤天師；改編自乾坤術數與天師稱號，不對應特定宗派、真人或歷史人物
```

遊方客、Lv.5／Lv.25／Lv.50 門檻、唯一後繼路線及轉職不重設等級，均是第 5 項導入前的歷史設計，不再是 Runtime 有效規則。

遊方客達 Lv.5 時進入四個第一階職業的選擇頁；第一階與第二階達到下一階門檻後，依既定的唯一後繼路線自動轉職並顯示成功頁，不再提供分支選擇。

三階職業的能力數值、技能與裝備限制均以 `PROJECT_SPEC.md` 為準。技能由目前職階自動賦予，不提供玩家手動配置；升階後以新職階技能完整覆蓋前階技能。進階職業可使用本路線前階裝備，並逐階增加專用武器與飾品類型。

御靈師第一階只使用靈狐襲與紙將衝陣；靈體只作為技能演出與傷害來源，不建立獨立戰鬥單位。四個第一階職業以同裝備等級下整體勝率接近為初版目標，但保留對不同敵人類型的相剋差異。

### 6.1 轉職文案語氣與意象

轉職文案採用荒誕武俠喜劇語氣：以一本正經的修行敘述搭配突兀、生活化的比喻，讓角色成長具備戲劇感與反差幽默。風格參考香港武俠喜劇的節奏與誇張感，但所有句子均為本作原創，不直接引用電影台詞或重現特定角色對白。文案的功能是降低職業選擇的生硬感，同時讓玩家在閱讀笑點時立即辨識各職業的戰鬥定位。

```text
轉職文案設計理由
├─ 重裝系
│  ├─ 金剛力士：使用「鋼鐵般的意志」與一拳解決問題，將厚重、防禦與直接的戰鬥方式轉為誇張承諾
│  ├─ 護法金剛：以「需要蓋章的正義」表現從武力轉為守護職責，保留護法的宗教意象但加入官僚式反差
│  └─ 鎮獄神將：以地府公文、十八層牢獄與老闆式口吻，放大鎮守幽冥的權威感
│
├─ 敏捷系
│  ├─ 飛燕劍客：以追不到的車尾燈與飛燕劍影，將速度與輕功翻譯成現代生活中直觀且帶笑點的畫面
│  ├─ 流雲劍俠：以影子加班、踏雲而行，表現速度提升後的飄逸與不受拘束
│  └─ 凌霄劍仙：以月光來不及反射、凡間放不下劍鞘，呈現由武俠跨入仙俠的誇張飛升
│
├─ 召喚系
│  ├─ 御靈師：以狐仙聊天、紙人談工作，將駕馭靈體的能力轉為日常人脈笑話
│  ├─ 通幽使：以代收陰間包裹與走後門，表現通達幽冥的便利感與民間鬼故事氣質
│  └─ 萬靈宗師：以路邊石頭也想拜師、萬靈排隊報到，放大統御萬物的階級感
│
└─ 法術系
   ├─ 方士：以「一張符不夠就再貼一張」，表現方術實用、直接又有點土法煉鋼的喜劇感
   ├─ 五行術士：以金木水火土輪流加班，將五行運轉轉化為容易理解的職場比喻
   └─ 乾坤天師：以替天地重新排版、缺少一張名片，表現掌握術數後的宏大能力與市井反差
```

轉職成功文案維持同一語氣，但隨階級提高逐步放大尺度：第一階是力量找到用途，第二階是能力與麻煩同步增加，第三階則進入超出常人理解的仙俠誇張感。實際顯示文字與各職業選項對應以 `PROJECT_SPEC.md` 為準。

```text
進階職業內容關係
├─ 護法金剛：新增禪杖與護法系飾品；使用護法棍、伏魔震、金剛伏魔棍
├─ 鎮獄神將：新增戰戟與神將系飾品；使用鎮獄破、神將怒、神將戰戟
├─ 流雲劍俠：新增長劍與劍俠系飾品；使用流雲十三式、雲蹤斬、流雲快劍
├─ 凌霄劍仙：新增飛劍與劍仙系飾品；使用凌霄一劍、劍落九霄、御劍凌空
├─ 通幽使：新增魂燈與通幽系飾品；使用幽冥鬼卒、攝魂靈獸、幽燈引魂
├─ 萬靈宗師：新增萬靈譜與宗師系飾品；使用萬靈朝宗、神將敕令、萬靈共鳴
├─ 五行術士：新增拂塵與五行系飾品；使用五行烈焰、水雷法、五行咒
└─ 乾坤天師：新增八卦鏡與天師系飾品；使用乾坤雷劫、天罡鎮煞、乾坤法印
```

## 7. 後續內容方向

```text
內容擴充順序
├─ 1. 《聊齋志異》地區
│  └─ 完成荒寺、狐鬼與人鬼故事的初期成長區
│
├─ 2. 《山海經》地區
│  └─ 建立上古山川、異獸與奇物的中階探索區
│
├─ 3. 《西遊記》地區
│  └─ 建立妖王洞府、法寶與修行題材的高階區域
│
└─ 4. 《封神演義》地區
   └─ 建立仙門、陣法、神將與封神題材的高階內容
```

以上僅定義內容方向，不代表已核准具體角色、怪物、職業、技能或數值。新增內容仍須遵守 MVP 範圍，不因題材規劃提前建立尚未需要的系統。

## 8. 尚待決策

```text
內容待決策事項
├─ 御靈系未來是否建立具有獨立 HP 與行動順序的召喚物
├─ 原典人物是否作為 NPC、敵人或僅保留背景身分
├─ 同名角色或跨作品相似設定的區分方式
├─ 佛教、道教、民間信仰與文學虛構的呈現界線
└─ 多來源融合內容的資料表示方式
```
