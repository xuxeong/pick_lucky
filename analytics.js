// GA4 + Microsoft Clarity 통합 로더
// 각 ID는 실제 발급 받은 값으로 교체하세요. 빈 문자열이면 해당 도구는 로드되지 않습니다.
(function () {
  var GA_ID = "";          // 예: "G-XXXXXXXXXX"
  var CLARITY_ID = "";     // 예: "abcd1234ef"

  if (GA_ID) {
    var s1 = document.createElement("script");
    s1.async = true;
    s1.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
    document.head.appendChild(s1);

    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag("js", new Date());
    gtag("config", GA_ID);
    window.gtag = gtag;
  }

  if (CLARITY_ID) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", CLARITY_ID);
  }
})();
