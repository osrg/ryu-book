.. _ch_introduction_example:

應用案例
========

本章介紹幾個使用 Ryu 作為產品或服務的案例。

Stratosphere SDN Platform (Stratosphere)
------------------------------------------------------------------------------------------------

Stratosphere SDN Platform（以下簡稱SSP） 是 Stratosphere 公司所開發的軟體。
經由 SSP 可以建構 Edge Overlay-model 的虛擬網路，它使用到的 Tunnelling 技術有：VXLAN、STT 和 MPLS。 

每一種通道協定可在 VLAN 間相互轉換。
因為每一種 Tunnelling 協定的 ID 通常都大於 VLAN 的 12 bits ，所以使用 L2 segments 來管理而不直接使用 VLAN。而且，SSP 可以和其他軟體如：OpenStack、CloudStack 或 IaaS 協同運作。

在 1.1.4 的版本中，SSP 使用 OpenFlow 實作它的功能並嵌入 Ryu 做為它的 Controller。其中一個理由是為了支援 OpenFlow 1.1 之後的版本。為了在 SSP 之上支援 MPLS，考慮導入已支援 OpenFlow 1.1 的框架在協定層。


.. NOTE::

    OpenFlow 協定本身支援的程度也是一個非常重要的考慮點。由於規範內有許多列為選項的功能，
    因此必須注意交換器對於該功能的支援程度是否足夠。


開發語言 Python 也是一個很重要的原因。Stratosphere 所用的開發語言就是 Python，許多 SSP 的元件也都是使用 Python 所撰寫。Python 本身的自我描述能力很高，對於習慣使用的開發者來說，可以大幅提升開發的效率。

軟體是由多個 Ryu 應用程式所組成，並透過 REST API 與其他的 SSP 元件溝通。
將軟體透過切割功能的方式分為多個應用程式，最基本的方法就是保持良好的原始碼。

SmartSDN Controller （NTT COMWARE）
----------------------------------------------------------------------

「SmartSDN Controller」 是一個提供集中管理功能（網路虛擬化/最佳化）的 SDN Controller。


.. only:: latex

    .. image:: images/introduction_example/fig1.png
        :align: center

.. only:: epub

    .. image:: images/introduction_example/fig1.png
        :align: center

.. only:: not latex and not epub

    .. image:: images/introduction_example/fig1.png
        :scale: 70 %
        :align: center


「SmartSDN Controller」 有以下兩個特徵。

1. 擁有彈性的虛擬網路路由管理

    在相同的實體網路中建構多個虛擬網路，可以提供一個有彈性的環境以回應使用者對於變動性的要求，設備則可以被有效的利用以降低購買成本。而且每一台裝置、交換器、路由器的設定均集中管理之後，可以清楚的知道整體網路目前的狀態。當網路發生故障或者通訊狀況發生改變時，可以做相對應的變更處置。

    藉由注重使用者的客戶體驗品質（「QoE」：Quality of Experience ）、網路通訊品質（ 頻寬、延遲、封包丟失、流量變化），判斷客戶體驗品質後選擇較好的路由以達到維持穩定的服務。

2. 確保網路的高度彈性及可用性

    為了在 Controller 發生故障的時候服務可以持續提供，備援的設定是必要的。主動產生封包並在節點間通訊，得以早期發現一般的監控無法及時發現的網路問題，並進行各種檢驗（ 路由測試、線路測試...等）。

    另外經由網路設計和狀態確認的視覺化圖形界面（ GUI ），讓即使沒有專業技能的操作人員都得以進行控制，降低網路運用的成本。

因此在「SmartSDN Controller」的開發上所選定的框架必須滿足下列的條件。

* 框架必須盡可能的支援 OpenFlow 規範的定義
* 框架必須隨時更新以追上不斷更新的 OpenFlow 版本

在這之中 Ryu 是：

* 全面的支援各種 OpenFlow 版本
* 最快的跟上 OpenFlow 所發佈的新版本。而且社群相當活躍快速回應及解決臭蟲。
* sample code / 文件均相當豐富。

由於以上的特徵，所以是相當適合採用的開發框架。
