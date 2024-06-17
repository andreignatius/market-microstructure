import numpy as np
from collections import defaultdict
import pandas as pd
from datetime import datetime

transactions = [
    ["Buy 0.1307578568473444 btc at 57357.93 on 2024-05-02 05:41:00",
    "Sell 0.1307578568473444 btc at 57718.55 on 2024-05-02 06:29:00 (Model predicted sell)",
    ],["Buy 0.13007033683534708 btc at 57661.11 on 2024-05-02 06:30:00",
    "Sell 0.13007033683534708 btc at 57969.8 on 2024-05-02 08:30:00 (Model predicted sell)",
    ],["Buy 0.1295336563845153 btc at 57900.01 on 2024-05-02 08:31:00",
    "Sell 0.1295336563845153 btc at 58221.8 on 2024-05-02 11:05:00 (Model predicted sell)",
    ],["Buy 0.12882567155534325 btc at 58218.21 on 2024-05-02 11:06:00",
    "Sell 0.12882567155534325 btc at 58541.55 on 2024-05-02 11:44:00 (Model predicted sell)",
    ],["Buy 0.127998470844935 btc at 58594.45 on 2024-05-02 11:45:00",
    "Sell 0.127998470844935 btc at 58942.19 on 2024-05-02 12:15:00 (Model predicted sell)",
    ],["Buy 0.1270058886703635 btc at 59052.38 on 2024-05-02 12:18:00",
    "Sell 0.1270058886703635 btc at 59394.42 on 2024-05-02 15:16:00 (Model predicted sell)",
    ],["Buy 0.12636897618045895 btc at 59350.01 on 2024-05-02 15:17:00",
    "Sell 0.12636897618045895 btc at 59664.0 on 2024-05-03 02:12:00 (Model predicted sell)",
    ],["Buy 0.12551891611905552 btc at 59751.95 on 2024-05-03 02:14:00",
    "Sell 0.12551891611905552 btc at 60099.0 on 2024-05-03 12:34:00 (Model predicted sell)",
    ],["Buy 0.12456814300954308 btc at 60208.01 on 2024-05-03 12:35:00",
    "Sell 0.12456814300954308 btc at 60624.56 on 2024-05-03 12:46:00 (Model predicted sell)",
    ],["Buy 0.12385033859031233 btc at 60556.96 on 2024-05-03 12:47:00",
    "Sell 0.12385033859031233 btc at 60875.91 on 2024-05-03 13:03:00 (Model predicted sell)",
    ],["Buy 0.12300958195439592 btc at 60970.86 on 2024-05-03 13:05:00",
    "Sell 0.12300958195439592 btc at 61344.01 on 2024-05-03 13:30:00 (Model predicted sell)",
    ],["Buy 0.12214186011630185 btc at 61404.01 on 2024-05-03 13:32:00",
    "Sell 0.12214186011630185 btc at 61723.97 on 2024-05-03 13:46:00 (Model predicted sell)",
    ],["Buy 0.12163084584198466 btc at 61661.99 on 2024-05-03 13:47:00",
    "Sell 0.12163084584198466 btc at 61983.99 on 2024-05-03 16:27:00 (Model predicted sell)",
    ],["Buy 0.121014059090681 btc at 61976.27 on 2024-05-03 16:28:00",
    "Sell 0.121014059090681 btc at 62376.14 on 2024-05-03 20:16:00 (Model predicted sell)",
    ],["Buy 0.1201583398539259 btc at 62417.64 on 2024-05-03 20:17:00",
    "Sell 0.1201583398539259 btc at 62754.02 on 2024-05-03 20:24:00 (Model predicted sell)",
    ],["Buy 0.11952204568196331 btc at 62749.93 on 2024-05-03 20:25:00",
    "Sell 0.11952204568196331 btc at 63151.0 on 2024-05-03 20:49:00 (Model predicted sell)",
    ],["Buy 0.11879118094272681 btc at 63136.0 on 2024-05-03 20:50:00",
    "Sell 0.11879118094272681 btc at 63566.01 on 2024-05-04 01:29:00 (Model predicted sell)",
    ],["Buy 0.11822242651057524 btc at 63439.74 on 2024-05-04 01:30:00",
    "Sell 0.11822242651057524 btc at 63919.99 on 2024-05-04 10:46:00 (Model predicted sell)",
    ],["Buy 0.1173435118660106 btc at 63914.91 on 2024-05-04 10:47:00",
    "Sell 0.1173435118660106 btc at 64290.05 on 2024-05-04 10:58:00 (Model predicted sell)",
    ],["Buy 0.11642280229064192 btc at 64420.37 on 2024-05-04 11:00:00",
    "Sell 0.11642280229064192 btc at 64876.0 on 2024-05-06 08:18:00 (Model predicted sell)",
    ],["Buy 0.11549920836842584 btc at 64935.51 on 2024-05-06 08:20:00",
    "Sell 0.11549920836842584 btc at 65269.82 on 2024-05-06 08:25:00 (Model predicted sell)",
    ],["Buy 0.11477716167097794 btc at 65344.01 on 2024-05-06 08:26:00",
    "Sell 0.11477716167097794 btc at 63335.02 on 2024-05-06 14:57:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11841789897595359 btc at 63335.02 on 2024-05-06 14:57:00",
    "Sell 0.11841789897595359 btc at 63673.53 on 2024-05-06 15:45:00 (Model predicted sell)",
    ],["Buy 0.11788745677459918 btc at 63620.0 on 2024-05-06 15:46:00",
    "Sell 0.11788745677459918 btc at 63950.47 on 2024-05-07 01:50:00 (Model predicted sell)",
    ],["Buy 0.11736336166224076 btc at 63904.1 on 2024-05-07 01:51:00",
    "Sell 0.11736336166224076 btc at 64280.0 on 2024-05-07 08:23:00 (Model predicted sell)",
    ],["Buy 0.1167275569482623 btc at 64252.18 on 2024-05-07 08:24:00",
    "Sell 0.1167275569482623 btc at 62298.83 on 2024-05-07 23:05:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12038749363350804 btc at 62298.83 on 2024-05-07 23:05:00",
    "Sell 0.12038749363350804 btc at 62625.25 on 2024-05-08 00:37:00 (Model predicted sell)",
    ],["Buy 0.11959876051033907 btc at 62709.68 on 2024-05-08 00:38:00",
    "Sell 0.11959876051033907 btc at 60805.99 on 2024-05-09 10:59:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12334311142701566 btc at 60805.99 on 2024-05-09 10:59:00",
    "Sell 0.12334311142701566 btc at 61150.81 on 2024-05-09 11:44:00 (Model predicted sell)",
    ],["Buy 0.12268894916097117 btc at 61130.2 on 2024-05-09 11:45:00",
    "Sell 0.12268894916097117 btc at 61517.33 on 2024-05-09 12:31:00 (Model predicted sell)",
    ],["Buy 0.12196470504055734 btc at 61493.2 on 2024-05-09 12:33:00",
    "Sell 0.12196470504055734 btc at 61896.36 on 2024-05-09 15:09:00 (Model predicted sell)",
    ],["Buy 0.12110631099519353 btc at 61929.06 on 2024-05-09 15:10:00",
    "Sell 0.12110631099519353 btc at 62270.0 on 2024-05-09 15:28:00 (Model predicted sell)",
    ],["Buy 0.12058536961827496 btc at 62196.6 on 2024-05-09 15:29:00",
    "Sell 0.12058536961827496 btc at 62511.88 on 2024-05-09 16:17:00 (Model predicted sell)",
    ],["Buy 0.12002033624577348 btc at 62489.41 on 2024-05-09 16:18:00",
    "Sell 0.12002033624577348 btc at 62802.01 on 2024-05-09 21:11:00 (Model predicted sell)",
    ],["Buy 0.11952455998626901 btc at 62748.61 on 2024-05-09 21:12:00",
    "Sell 0.11952455998626901 btc at 63220.55 on 2024-05-09 22:47:00 (Model predicted sell)",
    ],["Buy 0.11864220169553943 btc at 63215.28 on 2024-05-09 22:48:00",
    "Sell 0.11864220169553943 btc at 61285.99 on 2024-05-10 14:51:00 (Margin call / stop-loss triggered)",
    ]
    # ],["Buy 0.1223770718234298 btc at 61285.99 on 2024-05-10 14:51:00"
]

transactions = [
    ["Buy 0.1307578568473444 btc at 57357.93 on 2024-05-02 05:41:00",
    "Sell 0.1307578568473444 btc at 59079.0 on 2024-05-02 14:39:00 (Model predicted sell)",
    ],["Buy 0.12701931066112027 btc at 59046.14 on 2024-05-02 14:41:00",
    "Sell 0.12701931066112027 btc at 60875.91 on 2024-05-03 13:03:00 (Model predicted sell)",
    ],["Buy 0.12300958195439592 btc at 60970.86 on 2024-05-03 13:05:00",
    "Sell 0.12300958195439592 btc at 62805.17 on 2024-05-03 20:26:00 (Model predicted sell)",
    ],["Buy 0.11938378863657347 btc at 62822.6 on 2024-05-03 20:27:00",
    "Sell 0.11938378863657347 btc at 64876.0 on 2024-05-06 08:18:00 (Model predicted sell)",
    ],["Buy 0.11549920836842584 btc at 64935.51 on 2024-05-06 08:20:00",
    "Sell 0.11549920836842584 btc at 62986.67 on 2024-05-06 17:42:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11907281334288668 btc at 62986.67 on 2024-05-06 17:42:00",
    "Sell 0.11907281334288668 btc at 61066.0 on 2024-05-08 23:03:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12281793469361019 btc at 61066.0 on 2024-05-08 23:03:00",
    "Sell 0.12281793469361019 btc at 62917.99 on 2024-05-09 22:38:00 (Model predicted sell)",
    ],["Buy 0.11928543254488314 btc at 62874.4 on 2024-05-09 22:39:00",
    "Sell 0.11928543254488314 btc at 60980.13 on 2024-05-10 14:55:00 (Margin call / stop-loss triggered)",
    ]# "Buy 0.12248899599689629 btc at 61229.99 on 2024-05-10 14:58:00"
]

transactions = [
    ["Buy 0.1307578568473444 btc at 57357.93 on 2024-05-02 05:41:00",
    "Sell 0.1307578568473444 btc at 58541.55 on 2024-05-02 11:44:00 (Model predicted sell)",
    ],["Buy 0.127998470844935 btc at 58594.45 on 2024-05-02 11:45:00",
    "Sell 0.127998470844935 btc at 59781.1 on 2024-05-03 02:13:00 (Model predicted sell)",
    ],["Buy 0.12551891611905552 btc at 59751.95 on 2024-05-03 02:14:00",
    "Sell 0.12551891611905552 btc at 61152.34 on 2024-05-03 13:04:00 (Model predicted sell)",
    ],["Buy 0.12300958195439592 btc at 60970.86 on 2024-05-03 13:05:00",
    "Sell 0.12300958195439592 btc at 62253.33 on 2024-05-03 20:15:00 (Model predicted sell)",
    ],["Buy 0.1201583398539259 btc at 62417.64 on 2024-05-03 20:17:00",
    "Sell 0.1201583398539259 btc at 63736.17 on 2024-05-04 10:42:00 (Model predicted sell)",
    ],["Buy 0.1175120167788358 btc at 63823.26 on 2024-05-04 10:44:00",
    "Sell 0.1175120167788358 btc at 65269.82 on 2024-05-06 08:25:00 (Model predicted sell)",
    ],["Buy 0.11477716167097794 btc at 65344.01 on 2024-05-06 08:26:00",
    "Sell 0.11477716167097794 btc at 63929.95 on 2024-05-06 10:48:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11731590592515714 btc at 63929.95 on 2024-05-06 10:48:00",
    "Sell 0.11731590592515714 btc at 62558.01 on 2024-05-07 23:02:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11988872408185618 btc at 62558.01 on 2024-05-07 23:02:00",
    "Sell 0.11988872408185618 btc at 61200.0 on 2024-05-08 22:12:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12254901960784313 btc at 61200.0 on 2024-05-08 22:12:00",
    "Sell 0.12254901960784313 btc at 62429.78 on 2024-05-09 16:06:00 (Model predicted sell)",
    ],["Buy 0.12019232695389856 btc at 62399.99 on 2024-05-09 16:07:00",
    "Sell 0.12019232695389856 btc at 61022.01 on 2024-05-10 14:52:00 (Margin call / stop-loss triggered)",
    ]
    #"Buy 0.12290647259898518 btc at 61022.01 on 2024-05-10 14:52:00"
]


transactions = [
    ["Buy 0.1307578568473444 btc at 57357.93 on 2024-05-02 05:41:00",
    "Sell 0.1307578568473444 btc at 57941.92 on 2024-05-02 08:28:00 (Model predicted sell)",
    ],["Buy 0.12952057011155693 btc at 57905.86 on 2024-05-02 08:29:00",
    "Sell 0.12952057011155693 btc at 58541.55 on 2024-05-02 11:44:00 (Model predicted sell)",
    ],["Buy 0.127998470844935 btc at 58594.45 on 2024-05-02 11:45:00",
    "Sell 0.127998470844935 btc at 59253.68 on 2024-05-02 14:43:00 (Model predicted sell)",
    ],["Buy 0.12655861148666206 btc at 59261.08 on 2024-05-02 14:44:00",
    "Sell 0.12655861148666206 btc at 59916.01 on 2024-05-03 02:15:00 (Model predicted sell)",
    ],["Buy 0.1253216798652675 btc at 59845.99 on 2024-05-03 02:16:00",
    "Sell 0.1253216798652675 btc at 59220.0 on 2024-05-03 07:39:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12664640324214793 btc at 59220.0 on 2024-05-03 07:39:00",
    "Sell 0.12664640324214793 btc at 59910.0 on 2024-05-03 12:33:00 (Model predicted sell)",
    ],["Buy 0.12456814300954308 btc at 60208.01 on 2024-05-03 12:35:00",
    "Sell 0.12456814300954308 btc at 60875.91 on 2024-05-03 13:03:00 (Model predicted sell)",
    ],["Buy 0.12300958195439592 btc at 60970.86 on 2024-05-03 13:05:00",
    "Sell 0.12300958195439592 btc at 61624.0 on 2024-05-03 13:35:00 (Model predicted sell)",
    ],["Buy 0.12180068179149639 btc at 61576.01 on 2024-05-03 13:36:00",
    "Sell 0.12180068179149639 btc at 62253.33 on 2024-05-03 20:15:00 (Model predicted sell)",
    ],["Buy 0.1201583398539259 btc at 62417.64 on 2024-05-03 20:17:00",
    "Sell 0.1201583398539259 btc at 63048.0 on 2024-05-03 20:46:00 (Model predicted sell)",
    ],["Buy 0.11901361515757403 btc at 63018.0 on 2024-05-03 20:47:00",
    "Sell 0.11901361515757403 btc at 62384.46 on 2024-05-03 21:36:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12022224765590661 btc at 62384.46 on 2024-05-03 21:36:00",
    "Sell 0.12022224765590661 btc at 63064.5 on 2024-05-03 23:18:00 (Model predicted sell)",
    ],["Buy 0.11904571053702155 btc at 63001.01 on 2024-05-03 23:19:00",
    "Sell 0.11904571053702155 btc at 63736.17 on 2024-05-04 10:42:00 (Model predicted sell)",
    ],["Buy 0.1175120167788358 btc at 63823.26 on 2024-05-04 10:44:00",
    "Sell 0.1175120167788358 btc at 63180.89 on 2024-05-05 01:26:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11855435764719867 btc at 63262.12 on 2024-05-05 01:29:00",
    "Sell 0.11855435764719867 btc at 63917.35 on 2024-05-05 07:43:00 (Model predicted sell)",
    ],["Buy 0.11734151073283684 btc at 63916.0 on 2024-05-05 07:44:00",
    "Sell 0.11734151073283684 btc at 64588.15 on 2024-05-05 15:56:00 (Model predicted sell)",
    ],["Buy 0.11621370181237592 btc at 64536.28 on 2024-05-05 15:57:00",
    "Sell 0.11621370181237592 btc at 63875.69 on 2024-05-05 18:35:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11741556138180269 btc at 63875.69 on 2024-05-05 18:35:00",
    "Sell 0.11741556138180269 btc at 64520.99 on 2024-05-06 07:58:00 (Model predicted sell)",
    ],["Buy 0.11624046711929155 btc at 64521.42 on 2024-05-06 08:01:00",
    "Sell 0.11624046711929155 btc at 65269.82 on 2024-05-06 08:25:00 (Model predicted sell)",
    ],["Buy 0.11477716167097794 btc at 65344.01 on 2024-05-06 08:26:00",
    "Sell 0.11477716167097794 btc at 64685.62 on 2024-05-06 10:32:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11604570096322574 btc at 64629.71 on 2024-05-06 10:33:00",
    "Sell 0.11604570096322574 btc at 63929.95 on 2024-05-06 10:48:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11731590592515714 btc at 63929.95 on 2024-05-06 10:48:00",
    "Sell 0.11731590592515714 btc at 63271.97 on 2024-05-06 14:59:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11877426855242197 btc at 63144.99 on 2024-05-06 15:00:00",
    "Sell 0.11877426855242197 btc at 63800.01 on 2024-05-07 01:40:00 (Model predicted sell)",
    ],["Buy 0.11756138193247713 btc at 63796.46 on 2024-05-07 01:41:00",
    "Sell 0.11756138193247713 btc at 63145.69 on 2024-05-07 03:27:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11877295188317682 btc at 63145.69 on 2024-05-07 03:27:00",
    "Sell 0.11877295188317682 btc at 63794.45 on 2024-05-07 07:24:00 (Model predicted sell)",
    ],["Buy 0.11758801580571072 btc at 63782.01 on 2024-05-07 07:26:00",
    "Sell 0.11758801580571072 btc at 63142.91 on 2024-05-07 13:58:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11877818111328729 btc at 63142.91 on 2024-05-07 13:58:00",
    "Sell 0.11877818111328729 btc at 63867.94 on 2024-05-07 14:58:00 (Model predicted sell)",
    ],["Buy 0.11686218489280464 btc at 64178.16 on 2024-05-07 15:01:00",
    "Sell 0.11686218489280464 btc at 63532.18 on 2024-05-07 16:33:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11805041161817523 btc at 63532.18 on 2024-05-07 16:33:00",
    "Sell 0.11805041161817523 btc at 62873.09 on 2024-05-07 18:38:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11928791793118487 btc at 62873.09 on 2024-05-07 18:38:00",
    "Sell 0.11928791793118487 btc at 62158.0 on 2024-05-08 00:32:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12066025290389008 btc at 62158.0 on 2024-05-08 00:32:00",
    "Sell 0.12066025290389008 btc at 62798.86 on 2024-05-08 02:25:00 (Model predicted sell)",
    ],["Buy 0.11944577161968466 btc at 62790.0 on 2024-05-08 02:26:00",
    "Sell 0.11944577161968466 btc at 62150.0 on 2024-05-08 06:26:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12067578439259855 btc at 62150.0 on 2024-05-08 06:26:00",
    "Sell 0.12067578439259855 btc at 62786.01 on 2024-05-08 14:48:00 (Model predicted sell)",
    ],["Buy 0.11957528771009976 btc at 62721.99 on 2024-05-08 14:49:00",
    "Sell 0.11957528771009976 btc at 62020.0 on 2024-05-08 15:15:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12092873266688164 btc at 62020.0 on 2024-05-08 15:15:00",
    "Sell 0.12092873266688164 btc at 62664.2 on 2024-05-08 17:31:00 (Model predicted sell)",
    ],["Buy 0.11984657720572432 btc at 62580.01 on 2024-05-08 17:32:00",
    "Sell 0.11984657720572432 btc at 61878.35 on 2024-05-08 20:17:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12120555897175668 btc at 61878.35 on 2024-05-08 20:17:00",
    "Sell 0.12120555897175668 btc at 61200.0 on 2024-05-08 22:12:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12254901960784313 btc at 61200.0 on 2024-05-08 22:12:00",
    "Sell 0.12254901960784313 btc at 61896.36 on 2024-05-09 15:09:00 (Model predicted sell)",
    ],["Buy 0.12110631099519353 btc at 61929.06 on 2024-05-09 15:10:00",
    "Sell 0.12110631099519353 btc at 62599.89 on 2024-05-09 16:21:00 (Model predicted sell)",
    ],["Buy 0.11983190938406878 btc at 62587.67 on 2024-05-09 16:22:00",
    "Sell 0.11983190938406878 btc at 61945.34 on 2024-05-09 16:55:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12107448276173802 btc at 61945.34 on 2024-05-09 16:55:00",
    "Sell 0.12107448276173802 btc at 62583.03 on 2024-05-09 20:07:00 (Model predicted sell)",
    ],["Buy 0.11982744847419716 btc at 62590.0 on 2024-05-09 20:08:00",
    "Sell 0.11982744847419716 btc at 63220.55 on 2024-05-09 22:47:00 (Model predicted sell)",
    ],["Buy 0.11864220169553943 btc at 63215.28 on 2024-05-09 22:48:00",
    "Sell 0.11864220169553943 btc at 62507.99 on 2024-05-10 14:11:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.11998466116091719 btc at 62507.99 on 2024-05-10 14:11:00",
    "Sell 0.11998466116091719 btc at 61813.34 on 2024-05-10 14:36:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12133303264311555 btc at 61813.34 on 2024-05-10 14:36:00",
    "Sell 0.12133303264311555 btc at 61022.01 on 2024-05-10 14:52:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12290647259898518 btc at 61022.01 on 2024-05-10 14:52:00",
    "Sell 0.12290647259898518 btc at 60402.61 on 2024-05-10 17:25:00 (Margin call / stop-loss triggered)",
    ],["Buy 0.12416681994370773 btc at 60402.61 on 2024-05-10 17:25:00",
    "Sell 0.12416681994370773 btc at 61023.17 on 2024-05-11 01:13:00 (Model predicted sell)",
    ]#"Buy 0.12297333790466221 btc at 60988.83 on 2024-05-11 01:15:00"
]

# Function to parse dates from the transaction entries
def parse_date(transaction):
    # Assumes the date is always in the same position in the string
    transaction = transaction.split(' on ')[1].split(' ')[0] + ' ' + transaction.split(' on ')[1].split(' ')[1]
    return datetime.strptime(transaction, '%Y-%m-%d %H:%M:%S')

starting_principal = 10000

# Initialize a dictionary to hold daily PnL
daily_pnl = defaultdict(float)
pnl_logs = []
holding_periods = []
# Parse data and compute PnL
for buy, sell in transactions:
    buy_price = float(buy.split(' at ')[1].split(' on ')[0])
    sell_price = float(sell.split(' at ')[1].split(' on ')[0])
    amount = float(buy.split(' ')[1])
    pnl = amount * (sell_price - buy_price)
    pnl_logs.append(pnl)
    trade_date = sell.split(' on ')[1].split(' ')[0]
    buy_date = parse_date(buy)
    sell_date = parse_date(sell)
    # Calculate the difference in hours or another suitable time unit
    duration = sell_date - buy_date
    holding_periods.append(duration.total_seconds() / 3600)  # converting seconds to hours

    daily_pnl[trade_date] += pnl
print("check pnl: ", pnl_logs)
winning_logs = []
losing_logs = []
for i in pnl_logs:
	if i >= 0:
		winning_logs.append(i)
	else:
		losing_logs.append(i)
print("avg win:", np.mean(winning_logs) , len(winning_logs))
print("avg loss: ", np.mean(losing_logs), len(losing_logs))
# Calculate the average holding period
average_holding_period = np.mean(holding_periods)
print(f"Average Holding Period (hours): {average_holding_period}")
# Convert the daily PnL into a pandas Series
daily_returns = pd.Series(daily_pnl).sort_index()

# Calculate cumulative returns
cumulative_returns = daily_returns.cumsum() + starting_principal

# Determine the running maximum
running_max = cumulative_returns.cummax()

# Calculate drawdown: difference between running max and current cumulative return
drawdowns = (running_max - cumulative_returns) / running_max

# Maximum drawdown
max_drawdown = drawdowns.max()

# Printing results
print("Daily PnL:", daily_returns)
print("Cumulative Returns:", cumulative_returns)
print("Maximum Drawdown:", max_drawdown)

# Calculate expected return and standard deviation
expected_return_daily = daily_returns.mean()
std_dev_daily = daily_returns.std()

# Assume risk-free rate and calculate Sharpe Ratio (assuming daily rate for simplicity)
risk_free_rate = 3.5 / 100 / 365  # Convert annual rate to a daily rate for simplicity
sharpe_ratio_daily = (expected_return_daily - risk_free_rate) / std_dev_daily if std_dev_daily else 0
annual_sharpe_ratio = sharpe_ratio_daily * np.sqrt(365)  # Annualize the daily Sharpe ratio

# Print additional statistics
print("Expected Daily Return:", expected_return_daily)
print("Daily Standard Deviation of Returns:", std_dev_daily)
print("Daily Sharpe Ratio:", sharpe_ratio_daily)
print("Annual Sharpe Ratio:", annual_sharpe_ratio)