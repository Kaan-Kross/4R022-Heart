# Contributing / Katkı Rehberi

Thanks for helping make 4R022 Heart better! / 4R022 Heart'ı geliştirmeye yardım ettiğiniz için teşekkürler!

## 🇬🇧 Ground rules
1. **The brand stays.** Pull requests that remove, hide, shorten or alter the Brand Elements (`4R022`, `4R022 Heart`, `4R022 PRESENTS` opening, closing card, logo, credits, `LICENSE`, `Docs/NOTICE.md`) are closed. See [LICENSE](../LICENSE) Section 4.
2. By contributing you agree your contribution is licensed under the 4R022 Heart License (Section 8).
3. **Keep it fast.** The scene must stay smooth with low CPU use: pre-render, then blit; no per-frame allocations in hot paths; text is never scaled during the hold.
4. Be kind — see [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md).

### Development
```bash
pip install -r Build/requirements.txt
python Main/Main.py --windowed             # test in a window
python Main/Main.py --selftest             # internal health check
python Main/Main.py --screenshot out/      # render preview PNGs offscreen
python -m py_compile Main/Main.py
```
Build your own app (no Python needed): `Build/Build_Windows.bat`, `Build/Build_macOS.command`, `bash Build/Build_Linux.sh` — see the README.

### Pull requests
- one topic per PR, clear description; mention the OS you tested on
- new phrases: keep native script and correct spelling; RTL languages need `RTL_CODES`
- update [Docs/CHANGELOG.md](../Docs/CHANGELOG.md) for user-visible changes

## 🇹🇷 Temel kurallar
1. **Marka kalır.** Marka unsurlarını (`4R022`, `4R022 Heart`, `4R022 PRESENTS` açılışı, kapanış kartı, logo, krediler, `LICENSE`, `Docs/NOTICE.md`) silen/gizleyen/değiştiren PR'lar kapatılır — [LICENSE](../LICENSE) Madde 4.
2. Katkı yaparak, katkınızın 4R022 Heart Lisansı (Madde 8) ile lisanslanmasını kabul edersiniz.
3. **Hızlı kalsın.** Sahne akıcı ve düşük CPU ile çalışmalı: önce hazırla, sonra bas; sıcak yollarda kare başına tahsis yok; bekleme evresinde yazılar ölçeklenmez.
4. Nazik olun — [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md).

### Geliştirme
Yukarıdaki komutlar geçerlidir. Python gerektirmeden derleme: README.

### Pull request
Her PR tek konu · test ettiğiniz işletim sistemini belirtin · yeni dillerde yazım doğru olsun (sağdan sola diller için `RTL_CODES`) · kullanıcıya görünen değişiklikleri [CHANGELOG](../Docs/CHANGELOG.md)'a ekleyin.
