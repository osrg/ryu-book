.. _ch_contribute:

協助專案開發
======================

開放原始碼最大的優點在於對開發專案的共同參與，本章將介紹如何參與 Ryu 專案的開發。

參與專案
----------------

Mailing list 是 Ryu 專案開發者主要聚集的地方。
因此首先就是要加入 Mailing list 來得到最新的消息。

https://lists.sourceforge.net/lists/listinfo/ryu-devel

在 Mailing list 中主要使用英文來進行溝通。
當你在使用 Ryu 上遇到了困難，包括不知道如何使用或發現了程式上的錯誤。
任何時候都歡迎在 Mailing list 上提出你的疑問。
千萬不需要對於遇到了麻煩而感到不好意思結果不敢發言。
因為使用 Open source 本身並提出疑問對於專案而言就是一種貢獻。

開發環境
----------------

接下來說明 Ryu 專案在開發的環境上需要注意的事情。

Python 版本
^^^^^^^^^^^^^^^^

目前 Ryu 專案支援 Python 2.6 以上的版本，並請勿使用比 2.7 更早之前的版本。

Python 3.0 以上的版本在目前尚未提供支援。但請小心撰寫程式碼以保持擴充性並隨時注意將來改版的可能。

程式碼撰寫風格（ Coding Style ）
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ryu 的原始碼是遵守 PEP8 的規範來開發。當你在送交程式碼時，請務必確認程式碼符合 PEP8 的規範。

http://www.python.org/dev/peps/pep-0008/

為了讓開發者更好的檢查自己的程式碼是否符合 PEP8 規範，這邊有個檢查器可以幫助開發者，請參考下述連結。

https://pypi.python.org/pypi/pep8

測試
^^^^^^^^^^^^^^^^

Ryu 專案本身提供自動化測試的工具，最容易也是最常使用的是單元測試（ Unit test ），該功能也同樣包含在 Ryu 專案內。
在送出程式碼之前，務必確認通過所有的單元測試，確保您的修改不會對現有的程式碼造成影響。
如果是增加的程式碼，請在單元測試及註解的地方詳細說明該功能。


.. rst-class:: console

::

    $ cd ryu/
    $ ./run_tests.sh


送交更新的程式碼
--------------------------------

因為新功能的增加、程式錯誤的修復而需要對原始碼進行修改時，請針對修改的部分製作更新檔並寄送到 Mailing list。，
我們可以先在 Mailing list 中進行討論是否更新的必要。


.. NOTE::

   Ryu 的原始碼目前存放在 GitHub 上進行託管。   
   但請注意 Pull request 並不是開發程序的必要條件。

在更新檔的格式上，我們期望收到如同更新 Linux Kernel 相同或類似的格式。
下面的例子是用來說明送交程式更新檔時所需要符合的格式。
請參閱相關的文件以達到該要求。

http://lxr.linux.no/linux/Documentation/SubmittingPatches

接下來說明整個流程。

1. 原始碼 Check out

 首先是從 Ryu 專案下載原始碼。
 你可以在 Github 上 fork 一份專案到自己的帳號。
 下面的例子說明如何複製一份專案到自己的工作環境中。


 .. rst-class:: console
 
 ::
 
     $ git clone https://github.com/osrg/ryu.git
     $ cd ryu/

2. 原始碼的修改及增加

 對 Ryu 的原始碼進行必要的修改。
 接著將變更的內容進行 Commit。


 .. rst-class:: console
 
 ::

     $ git commit -a``

3. 更新檔的製作

 對於變更的地方製作更新檔。
 不要忘記加入 Signed-off-by: 在即將送出的更新檔中。
 這個署名是用來辨認你對開放原始碼的貢獻，以及滿足相關的授權所使用。


 .. rst-class:: console
 
 ::
    
     $ git format-patch origin -s

4. 送出更新檔

 已經完成的更新檔，在確認過沒有問題之後，請寄送到 Mailing list。
 你可以使用自己熟悉的郵件軟體或寄送方法，或者也可以使用 git 內建的寄送郵件指令。


 .. rst-class:: console
    
 ::
    
     $ git send-email 0001-sample.patch

5. 等待回應

 等待開發團隊的討論以及對於更新檔的回應。
 原則上整個流程已經結束，若是你的更新檔有任何問題，你需要針對提問進行說明，必要時再次修改並送交更新檔。
