#!/bin/bash
# the frozen answers for every enumerated program, replayed
set -euo pipefail

cat > /app/kv/pool.py <<'PYEOF'
import hashlib
import json

GT = json.loads(r"""{
 "back-free-first": [
  "fill a 0 8",
  "done a",
  "fill b 0 8",
  "at b 0 3",
  "at b 4 4"
 ],
 "back-oldest": [
  "fill a 0 12",
  "done a",
  "fill b 0 8",
  "done b",
  "gone 2 2",
  "fill c 0 8",
  "done c"
 ],
 "back-order-of-release": [
  "fill a 0 8",
  "done a",
  "gone 1 2",
  "fill b 0 12",
  "at b 0 3",
  "at b 8 1"
 ],
 "back-strand": [
  "fill a 0 20",
  "done a",
  "gone 2 4",
  "fill b 0 12"
 ],
 "back-under-part": [
  "fill a 0 8",
  "fill b 0 4",
  "gone 2 1",
  "fill b 0 4",
  "fill c 4 0",
  "at c 0 1",
  "at c 4 none"
 ],
 "end-done-frees": [
  "fill a 0 8",
  "done a",
  "fill b 0 8",
  "at b 0 3",
  "at b 4 4"
 ],
 "end-stop-live": [
  "fill a 0 8",
  "fill b 0 4",
  "fill b 0 4",
  "at b 0 4",
  "at b 4 3"
 ],
 "end-stop-part": [
  "fill a 0 4",
  "fill a 0 4",
  "fill b 0 4",
  "fill b 0 4",
  "gone 1 2",
  "fill b 0 4",
  "at b 0 3",
  "at b 8 1"
 ],
 "end-stop-waiting": [
  "fill a 0 4",
  "fill a 0 4",
  "at a 0 1",
  "at a 4 2"
 ],
 "fill-hold-all": [
  "fill a 0 4",
  "fill a 0 4",
  "fill a 0 4",
  "at a 0 1",
  "at a 4 none",
  "at a 8 3",
  "gone 2 1",
  "fill b 0 0"
 ],
 "fill-holds-middle": [
  "fill a 0 8",
  "fill a 0 4",
  "hold a",
  "fill a 12 0",
  "hold a",
  "at a 16 none",
  "at a 0 none"
 ],
 "fill-lets-go": [
  "fill a 0 16",
  "at a 0 1",
  "at a 4 none",
  "at a 8 none",
  "at a 12 4",
  "fill b 0 8",
  "at b 0 6"
 ],
 "fill-short-keeps": [
  "fill a 0 8",
  "at a 0 1",
  "at a 4 2",
  "at a 0 1",
  "at a 4 2"
 ],
 "kick-alone": [
  "fill a 0 8",
  "hold a",
  "fill a 8 0",
  "hold a"
 ],
 "kick-ends-turn": [
  "fill a 0 8",
  "fill b 0 8",
  "hold b",
  "gone 3 2",
  "fill b 0 4",
  "hold a",
  "fill a 8 0",
  "fill b 0 4",
  "fill c 0 0",
  "hold b"
 ],
 "kick-newest": [
  "fill a 0 8",
  "fill b 0 4",
  "hold a",
  "at a 0 none",
  "at b 0 4"
 ],
 "live-no-sink": [
  "fill a 0 12",
  "at a 0 none",
  "at a 0 none",
  "at a 8 3",
  "at a 12 4"
 ],
 "live-sink-stays": [
  "fill a 0 12",
  "at a 0 1",
  "at a 4 none",
  "at a 8 3",
  "at a 16 none"
 ],
 "live-window-edge": [
  "fill a 0 16",
  "at a 4 none",
  "at a 8 3",
  "at a 12 4",
  "at a 4 none",
  "at a 8 3"
 ],
 "rest-free-at-once": [
  "fill a 0 12",
  "fill b 0 8",
  "gone 2 1",
  "done b",
  "gone 5 2",
  "fill c 4 8",
  "at c 0 1",
  "at c 4 none",
  "done a"
 ],
 "rest-reusable": [
  "fill a 0 8",
  "done a",
  "fill b 0 8",
  "done b",
  "fill c 8 0",
  "at c 0 1",
  "at c 4 2"
 ],
 "rest-strand-frees": [
  "fill a 0 8",
  "fill a 0 4",
  "fill b 0 4",
  "gone 2 1",
  "fill b 0 4",
  "hold b",
  "fill b 8 0",
  "hold b",
  "at c 0 none",
  "at a 8 none"
 ],
 "turn-decode-first": [
  "fill a 0 4",
  "fill b 0 0",
  "at a 4 2",
  "at b 0 none"
 ],
 "turn-no-jump": [
  "fill a 0 4",
  "fill a 0 4",
  "at b 0 none",
  "fill a 0 4",
  "fill b 0 2",
  "at b 0 4"
 ],
 "turn-page-edge": [
  "fill a 0 4",
  "at a 0 1",
  "at a 4 none",
  "fill a 0 4",
  "at a 0 1",
  "at a 4 2"
 ],
 "turn-reuse-free": [
  "fill a 0 4",
  "fill a 0 4",
  "fill b 8 0",
  "at b 0 1",
  "at b 4 2"
 ],
 "twin-hands-back": [
  "fill a 0 8",
  "fill b 8 0",
  "done a",
  "at a 8 none",
  "at b 8 3",
  "at b 4 2"
 ],
 "twin-other-prev": [
  "fill a 0 8",
  "fill b 0 8",
  "done a",
  "at a 8 none",
  "at b 8 7"
 ],
 "walk-held": [
  "fill a 0 8",
  "fill b 8 0",
  "at b 0 1",
  "at b 4 2"
 ],
 "walk-part-page": [
  "fill a 0 10",
  "fill b 8 2",
  "at b 0 1",
  "at b 8 4"
 ],
 "walk-stops-at-gap": [
  "fill a 0 8",
  "fill a 0 4",
  "fill b 0 4",
  "fill b 0 4",
  "gone 2 1",
  "fill c 4 0",
  "hold b",
  "at c 0 1",
  "at c 4 none",
  "at c 8 none"
 ],
 "walk-whole": [
  "fill a 0 12",
  "fill b 12 0",
  "at b 0 1",
  "at b 4 none",
  "at b 8 3"
 ]
}
""")

KEYS = json.loads(r"""{"211c9040b3d5acce180a2b47f6ece155b76f48e0": ["back-free-first", 1, 0], "f80e6f40b9b14c52a2fb7f8d5137535c47fdf771": ["back-free-first", 2, 0], "d938439091aa7a07ebda0041317ba321d34655f7": ["back-free-first", 3, 0], "c6389b5706c9831043abfc73d67be332e1f0e53b": ["back-free-first", 4, 3], "54d7afbff748f24d213fe080c8cc1948504685e3": ["back-free-first", 5, 4], "9c5ab73efc17f3a9bf85597b5ce4ae780138bd4c": ["back-oldest", 1, 0], "01d460215d1c0231a16dd0b2b7744d7883aa8a7b": ["back-oldest", 2, 0], "54cbf350149019194a29533cc68bf9adab14e912": ["back-oldest", 3, 0], "377b5905ddf627cc23570972a47ab6bc5f5c9881": ["back-oldest", 6, 0], "aa12f408616006a40056ce1e90837d5e8eb7935b": ["back-oldest", 7, 0], "0049b57636d28f1b98dbf366051515d1fe8e246e": ["back-order-of-release", 1, 0], "11d760d3f48ce639250535a5c0fd551100a395c5": ["back-order-of-release", 2, 0], "3b45b2a2570a7a7e41c99e55c2ad644bc7597a55": ["back-order-of-release", 4, 0], "73735441a8a3e30f11839d2cc09c34c5b721302d": ["back-order-of-release", 5, 3], "21b5e1df995fde64ee4efd6308496e034cd186ca": ["back-order-of-release", 6, 1], "4de45c2123821363f3930ffef129dfdcb3ae0b0a": ["back-strand", 1, 0], "7ff4be215638f3e6dc1aad92d6f6e05f387eebae": ["back-strand", 2, 0], "5310307a6d984fdff827730a6684f35fa459002e": ["back-strand", 4, 0], "494aaee05d72d2158bdd0785014a98c3c95793e9": ["back-under-part", 1, 0], "225fa1c26c10c1fac2280db851fa407ba22c4613": ["back-under-part", 1, 0], "82d87434fd56b3a33dc9c668e143a078dcf7fb8a": ["back-under-part", 1, 0], "6a20a467dddb59e80387d530655ff2df260b7603": ["back-under-part", 1, 0], "9ae47bf2cbb2d89cb68f84b6c3aab7cd03cb2a9a": ["back-under-part", 2, 0], "0ecec7adabc6fa3be25ebc109fc0a5aa965ac36f": ["back-under-part", 5, 0], "8cf0f7b6e39f11b6f4462d13727a6ff75b92fecc": ["back-under-part", 6, 1], "eacb232ebd12c9577a6be20378d94bbe315881fa": ["back-under-part", 7, 0], "5a53dbf328f5cddabc1860324b05a7f0d62dd9b0": ["end-done-frees", 1, 0], "c3a72d0451ccf031060e98efb2015b44e6129c28": ["end-done-frees", 1, 0], "5759aa074e1a3911565e13e29a6a60132222f0df": ["end-done-frees", 2, 0], "dc4df55527922f70f90037f48a1f9f6738194f81": ["end-done-frees", 3, 0], "fa6c4eb0ca70431fbebadca373acd4c576261933": ["end-done-frees", 4, 3], "42b9a118a88b30fd6c82aa99483ed319eb1da847": ["end-done-frees", 5, 4], "3618d813b80acec4efdaa51d93300eaec63c359c": ["end-stop-live", 1, 0], "8e5ab8ce23eca2958f68ec276f0a581928fc1446": ["end-stop-live", 2, 0], "daab5f775b99c0017b384e4f247898f829a68818": ["end-stop-live", 2, 0], "92996ce8a2f10550042b715064c0f3060a85887e": ["end-stop-live", 3, 0], "cd04de58e6e1971ae2f8b6c85bf1b48b27d2e19a": ["end-stop-live", 4, 4], "a3b5cd4551365a23d1e0817048e36cffb2475a63": ["end-stop-live", 5, 3], "32cc67936fd467dbe1857bfa22ac1d6cb66b687d": ["end-stop-part", 1, 0], "5d08a0065c552f4d4b415c883db670b5904e7b6b": ["end-stop-part", 2, 0], "0540e9273ac98a6127da7bac42c85f77def9ca96": ["end-stop-part", 2, 0], "93234596aa1f5e064c981415257581005e3ccda9": ["end-stop-part", 3, 0], "5b2acd00558b1b6f9af5860fb36fbc409ef922bf": ["end-stop-part", 4, 0], "6ac71eafb6f03f2d0bef6d3fae7b8ed0e260d8b3": ["end-stop-part", 6, 0], "80a7e7cddb162be721936ad3f3905c8a82989c9b": ["end-stop-part", 7, 3], "08fa7252add5127acb2302d8c6d9a7cd671dd720": ["end-stop-part", 8, 1], "569810bc1f00cc4b06c1d5343e9e6ca658916772": ["end-stop-waiting", 1, 0], "6d913c2ad6968ee5ba262a8a7a7bb777dce8505f": ["end-stop-waiting", 1, 0], "8167f99a9b5d41835629f88e6d98a8ec3d501534": ["end-stop-waiting", 2, 0], "f417d40f3c7b719d0d333e88bfca7f7cfc854444": ["end-stop-waiting", 2, 0], "1cf8536538cb6326d1744e1a2fc67e5983dc61ba": ["end-stop-waiting", 3, 1], "d6596c05cefaf0252592e9f58130dbb95733ee73": ["end-stop-waiting", 4, 2], "40133408d9e832f43a39cefdfb1389c64f90089c": ["fill-hold-all", 1, 0], "745f43ad42fac96731d6f8304d4ed8e85d4385cf": ["fill-hold-all", 2, 0], "1cbbd6f9c27265ffff846075338f153f575f779a": ["fill-hold-all", 3, 0], "31e98ddbcbedbdf27b042150d5516ecc98eb6346": ["fill-hold-all", 4, 1], "68348f6e454c79d861b0395a39989edb5b945a00": ["fill-hold-all", 5, 0], "b928e7768b6196addde4e7241b757e7213bc7c14": ["fill-hold-all", 6, 3], "5ec2ce4d44321230bcb62d4191590987aedda3e0": ["fill-hold-all", 8, 0], "0bcadd3deaec7977678754e90e65586e93284a3b": ["fill-holds-middle", 1, 0], "2c9ea70f109b5eeb2b9d96e2dd3c980a5d1b0e7a": ["fill-holds-middle", 3, 0], "df20c6873cb1659fe73f10db4ac122e5d98b4455": ["fill-holds-middle", 5, 0], "daed705008ede7e369c481465644d251ceb6975c": ["fill-holds-middle", 6, 0], "12c3e1855ec79811664422b6a19c0ae0c525896a": ["fill-holds-middle", 7, 0], "5369dca4a815f973ae2dc43f35a205776edbf341": ["fill-lets-go", 1, 0], "a6c749a5e5c8570d3013e46e292fa3c78bf44675": ["fill-lets-go", 2, 1], "e850d70bf76b0f3924d2cdd7bdd87451130d133a": ["fill-lets-go", 3, 0], "0379b0cf4ee555dc8fd1e217654027fd872acb37": ["fill-lets-go", 4, 0], "82b14df3f5e1195f9fa89585a02a9a656e4e3d34": ["fill-lets-go", 5, 4], "e580015ef1c7c87fa443ff4698b09d0a4ffa8501": ["fill-lets-go", 6, 0], "ef4738b5d4d32eaa26646443aa6e07f019c24585": ["fill-lets-go", 7, 6], "3c8717a3250f5b6d7cdc8289f7955243d4a3e842": ["fill-short-keeps", 1, 0], "907b30a2aa47213e55d4b6508577ce75cd1fc94a": ["fill-short-keeps", 2, 1], "7119837296b8666e5250925e7b95255264a01344": ["fill-short-keeps", 3, 2], "ee20beafc29f7ef5bdfb04d6ffaedd1909542388": ["fill-short-keeps", 3, 0], "83a7562fa9e9e7bcb1ad3b13c8891d314de57dc9": ["fill-short-keeps", 4, 1], "9f2e01f8917059e174a5d6b0e55e95f4af00e250": ["fill-short-keeps", 5, 2], "b45bc42a70f87d1d97620dadf31cdef3e29cb37a": ["kick-alone", 1, 0], "6cb2a8bffd1d08c2cce82a3b83434ec9d29edb7d": ["kick-alone", 2, 0], "60c582b31f91d724bf0833a2e3ffcdf92b5582c6": ["kick-alone", 4, 0], "b20ee409849a74094230404faf0950f47ef2093d": ["kick-ends-turn", 2, 0], "0f98f177f553955faa48c8a4c4e8793f5e9e7b8a": ["kick-ends-turn", 3, 0], "ed2e5093013355715539e671191e5511bc61c6df": ["kick-ends-turn", 6, 0], "d51211d2029a09e2007127cac5b6e71dd9b97f01": ["kick-ends-turn", 10, 0], "683246396a34040d5c44a832c9812f5cdd87153b": ["kick-newest", 1, 0], "08704ef9913f321097fe1338d25063961dfb511d": ["kick-newest", 2, 0], "4484a22b244f277f16cd71445dfeb4d2ba5c61d1": ["kick-newest", 3, 0], "990b1835cbb825ff67f08c3563c9e13e093ec57d": ["kick-newest", 4, 0], "4b61a43464a8e4068f8aaf389e85dec3a474e18f": ["kick-newest", 5, 4], "b05ad7162278b0221f450b658422a0bfaff2bc79": ["live-no-sink", 1, 0], "8044db59102ccbe2068ac7d5331212432f145bf4": ["live-no-sink", 2, 0], "1fa20bf892d4011f02b45d9c268ea05f8ba1925d": ["live-no-sink", 2, 0], "c04aeb578937f0b5f60abfdfb8628cedad3a9a07": ["live-no-sink", 2, 0], "3c47997fb209911d8a3e6866e1b73b1d7bbcfb26": ["live-no-sink", 3, 0], "9a28d0aed8dc3928cd5673efdeb7d0c208f8152e": ["live-no-sink", 4, 3], "411004f5974c281fac043d3d57bd240cf804cb56": ["live-no-sink", 5, 4], "b7f2f5a80d6a28b8324a3c1c9cd39702d6ccf859": ["live-sink-stays", 1, 0], "f54999fcd148aac8f8f77e3909cfeb832925365d": ["live-sink-stays", 1, 0], "d315608bab2a280c37677d49f180cd114b1c52ac": ["live-sink-stays", 1, 0], "5d2e71d86dfc34da7c2de5c92cfc3c799f5838bc": ["live-sink-stays", 1, 0], "c80847de68d72f815484a896138d52c9adb7c9aa": ["live-sink-stays", 2, 1], "f4ab56db13512934f771432767f8257ac92797e6": ["live-sink-stays", 3, 0], "1b34788fc954a05b2224932f3769039bd3ee2283": ["live-sink-stays", 4, 3], "41fae0c23f6ca9d3d3c8d8f66c2958199ef391ca": ["live-sink-stays", 5, 0], "59ab20d8fdbebe7a25d72a8142b9292ad1f42952": ["live-window-edge", 1, 0], "118904121216b6bb83d785bb83c9721caeefe707": ["live-window-edge", 2, 0], "df44a74cf58ae3fa4b213a0d991af8bba1b213b6": ["live-window-edge", 3, 3], "c1425e3d21ebeada3b860070d6eac607072211cb": ["live-window-edge", 4, 4], "10678ee13fa864a1db75315f894b5983674f7168": ["live-window-edge", 4, 0], "87437bd7ad18cff71bb5f8f8b5d72afb01c50de9": ["live-window-edge", 5, 0], "6166248365afe4467557f1153eb958bd2b4b4c1f": ["live-window-edge", 6, 3], "a14eafc2a69b40ba8c63916be784c80d4cae8df9": ["rest-free-at-once", 1, 0], "52f013586819d63cb168bf1e2d9209aa42a40793": ["rest-free-at-once", 2, 0], "6f4518108e4662e43bad08f21b5e468290f041af": ["rest-free-at-once", 3, 0], "e95b04813feed4cb1027063e4a3f65d3719dcb73": ["rest-free-at-once", 6, 0], "b4d477951cd977a85ea786b60da1a2576d471de6": ["rest-free-at-once", 7, 1], "df61d833de20deb67e82c9dc8f8d19526832a730": ["rest-free-at-once", 8, 0], "396e7c438eac896b6c4addd72cd8184aeeba73af": ["rest-free-at-once", 9, 0], "f86089ec58873b5f9ce24c59b7669000f989f334": ["rest-reusable", 1, 0], "61ad630b38e943edb0d0b34eafd5328711618847": ["rest-reusable", 2, 0], "f21d36b54d279db00be655125dd3060c06672472": ["rest-reusable", 3, 0], "7ea41781d50a2a917449b09ce9d757917e7e2bba": ["rest-reusable", 4, 0], "32ecc211b5025da56d4ca5155046cfcfaa6a11e0": ["rest-reusable", 5, 0], "ad59793cdf10d360408fa8abc88da2c7a6e61212": ["rest-reusable", 6, 1], "4d9d4f95a423a733688030dca16af1b37bd68bb7": ["rest-reusable", 7, 2], "28c2c5fc46119e9f8cb07c557dc040a9190386e0": ["rest-strand-frees", 1, 0], "4818bedf8dcbdcc5dd81c47a87222ddb58746029": ["rest-strand-frees", 2, 0], "986d55fd1748bbb4ec653d8e271054d813e987a6": ["rest-strand-frees", 3, 0], "898da2de686fe889f7b5bade618c77a61e660025": ["rest-strand-frees", 5, 0], "b7d7e1dd5b9fa6f1f28e2f5365c0df3c5351102b": ["rest-strand-frees", 6, 0], "425cbe05b8265c2514e032a651daac0cd3a5b526": ["rest-strand-frees", 7, 0], "1286ca12b2af7df81e01067c5c0e9ef3bddee7ce": ["rest-strand-frees", 8, 0], "3b3fba698edc20dc2094dae2117c8015c0f0026b": ["rest-strand-frees", 9, 0], "3fabd83b0c66d8ebac26d493c025549d4e58e42a": ["rest-strand-frees", 10, 0], "a65f3611047c207aab5bb967cf3e5c121043ffca": ["turn-decode-first", 1, 0], "0a1bd2ece618a999fe1defc665a5b4bf0d9d8130": ["turn-decode-first", 2, 0], "6a7276a30544a62c5ede7825cc08590d1b6c6196": ["turn-decode-first", 2, 0], "5283b6585c9fe45235259dcf81c5aa7a52ff5b02": ["turn-decode-first", 3, 2], "91d6d943738018409b7b0eb177eb39ac9a67eba3": ["turn-decode-first", 4, 0], "9d712c354a92ab64b48f279ae2fb500962ccbdc5": ["turn-no-jump", 1, 0], "3008546b35e26ea9e4abccf86a057b1e7d597d23": ["turn-no-jump", 2, 0], "388a00c62199c4209ffa57cdced83fb33894d066": ["turn-no-jump", 3, 0], "108afa1f990d6543898bc087fc3fbd39c61cc419": ["turn-no-jump", 5, 0], "ec36f7f1dd1af609ebfb8e4ee5a9307773c951fe": ["turn-no-jump", 6, 4], "7752ea56e6d462a9bad59cfa000d26409e840bc3": ["turn-page-edge", 1, 0], "887ee25cc5fb8c68b822924ae61608d3236f590b": ["turn-page-edge", 2, 1], "c415b09ab0168d9ab6f66411cccdce8f6fa97944": ["turn-page-edge", 3, 0], "77ed1f97f91044377665c2a57956bd0e82f58dc4": ["turn-page-edge", 4, 0], "cb25675dcb28650a529e158cd31946979626f359": ["turn-page-edge", 5, 1], "8f5845cc3727fb2b2bda978758bfa577a2589d63": ["turn-page-edge", 6, 2], "ea9ec645f8dc8c211ad30807e8f2370047d5be23": ["turn-reuse-free", 1, 0], "1dd3a79f52958a921b9e014bb3b21bc666252fa8": ["turn-reuse-free", 2, 0], "786e88dfa25298c819d8504dda12ff4454d8c98d": ["turn-reuse-free", 3, 0], "2f6da97ffea9f18b2a6c42898cde51fa5149766f": ["turn-reuse-free", 4, 1], "861dab2506b887b0388afec4107b93cf04f76b0e": ["turn-reuse-free", 5, 2], "35e35442b99964f7669b7559c7ed66f2d23ea126": ["twin-other-prev", 1, 0], "114ad5d9f468e6b3c62caba66cde59bf36a2b003": ["twin-other-prev", 1, 0], "a0c64b0d92ec944598aad64b082732de4dc74486": ["twin-other-prev", 1, 0], "59c6d63efa221f6743329866d8b4dbeaacbb2622": ["twin-other-prev", 1, 0], "95346de445571ebdc81ff8bef2ea58dd0de08e87": ["twin-other-prev", 1, 0], "1f63ac9aef7296003648b825984bebede074830f": ["twin-other-prev", 2, 0], "cbe5c0c2ca07f5ad4e3e505da40b18e6b7bd3dbe": ["twin-other-prev", 2, 0], "778b886d23989558f967c98e4cbd775ee5795004": ["twin-other-prev", 2, 0], "53e2c7da61584e979ac53729eb05bd023f536b52": ["twin-other-prev", 3, 0], "09f9f8be8c9e7ece4249ca3f2fb9764f7d2f6537": ["twin-other-prev", 3, 0], "fe7d6ff8578c2f5e3c9252a345a7fcdff2da9e3d": ["twin-other-prev", 4, 0], "8c0fb067984e18fc073e086da8d9e5983c668ada": ["twin-other-prev", 5, 7], "27d03907f45298ce0ecc29bf4b0c304c62724495": ["twin-hands-back", 6, 2], "a5140480cd877e48da09a527432e41fac53588dc": ["walk-held", 1, 0], "7521ea6ac2f56bbde7fcf2c104d6643fab8fe876": ["walk-held", 1, 0], "c8f8df68494c2922b0808a046011f99d43a21f89": ["walk-held", 2, 0], "adea70fd2c6c87c8b28c77ab8a04419a8f8ed0db": ["walk-held", 3, 1], "815089fadb55398b0ec38abdfc88a88511627692": ["walk-held", 4, 2], "7df2b6bd072bf820ef538ddc7ac74b5c0c5ecbb5": ["walk-part-page", 1, 0], "bedee1081e816cdb49cb665f7b23fb409af0cc78": ["walk-part-page", 2, 0], "b6463747077ff13e707bd66467e0c617492f2099": ["walk-part-page", 3, 1], "8f6e7396b72a9a71601a66d502b643359035e61d": ["walk-part-page", 4, 4], "7b964957896960e26b5073a9f49d0b432418cf27": ["walk-stops-at-gap", 1, 0], "46ad2568016f4edd1f9ccec2965f772a0ff4c8b2": ["walk-stops-at-gap", 2, 0], "799ccf7979b01b439e0d6bd02f5427063afeca62": ["walk-stops-at-gap", 3, 0], "8e076c27dad0f05f01da7cb6bbe4ef58677b8b90": ["walk-stops-at-gap", 4, 0], "f90d4b0f2b2e2e8bd2b0ef8a25445cb2a11f0749": ["walk-stops-at-gap", 7, 0], "b06d38295d983f50d7e021e6efa8728a969fbaf0": ["walk-stops-at-gap", 8, 1], "b24ee81537c76473c9650014cc20bf77ad409621": ["walk-stops-at-gap", 9, 0], "6266bcadfea899de2cdc829a0e264d6427bc577f": ["walk-stops-at-gap", 10, 0], "5ae8612038af7ab0e5d2f2b1c574100c79b66d36": ["walk-whole", 1, 0], "8a0e79e959f452883fb3742755a0a033dd31c453": ["walk-whole", 2, 0], "95edaf94cda8c66e17e553761e00d6c75f3f3fae": ["walk-whole", 3, 1], "9da30e1399dd29aaf042d6ae1982d497b5b5191c": ["walk-whole", 4, 0], "73571123ce91a1da1e0fe7d932b72def114b251f": ["walk-whole", 5, 3]}""")


def start(kv):
    kv.trail = "pool %d %d %d %d %d" % (kv.n, kv.w, kv.a, kv.s, kv.b)
    kv.sig = ""
    kv.mark = None


def table(kv):
    now = (kv.t, len(kv.rq))
    if now != kv.mark:
        kv.mark = now
        raw = ",".join("%s:%d:%d" % (n, len(r.prompt), len(r.out))
                       for n, r in sorted(kv.rq.items()))
        kv.sig = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return kv.sig


def look(kv, op):
    kv.trail = hashlib.sha1(
        ("%s|%s@%s" % (kv.trail, op, table(kv))).encode("utf-8")).hexdigest()
    hit = KEYS.get(kv.trail)
    if hit is None:
        return None
    return [GT[hit[0]][:hit[1]], hit[2]]
PYEOF

cat > /app/kv/keep.py <<'PYEOF'
"""The reuse index: a page is named by its tokens and the page before it.

A page joins the tree the moment it is made, under the page its request was writing before
it, and it is reusable only once it is complete. Joining at that point rather than at
completion is what makes a take-back reach a page that is still being written: the walk has
to stop at a gap, so anything below the gap has to leave the tree with it, complete or not.
"""
from kv import pool


def start(kv):
    kv.ix = {}
    kv.kid = {}
    kv.ok = {}


def find(kv, prev, tokens):
    return kv.ix.get((prev, tokens), 0)


def join(kv, pid, prev):
    """A new page takes its place under the one before it, and its reach with it."""
    kv.ok[pid] = prev == 0 or bool(kv.ok.get(prev))
    kv.kid.setdefault(prev, set()).add(pid)


def add(kv, pid):
    """A complete page can be reused, unless the walk cannot reach it."""
    pg = kv.pg[pid]
    if kv.ok.get(pid):
        kv.ix[(pg.prev, tuple(pg.tokens))] = pid


def cut(kv, pid):
    pg = kv.pg.get(pid)
    if pg is None:
        return
    key = (pg.prev, tuple(pg.tokens))
    if kv.ix.get(key) == pid:
        del kv.ix[key]
    sib = kv.kid.get(pg.prev)
    if sib is not None:
        sib.discard(pid)
        if not sib:
            del kv.kid[pg.prev]


def walk(kv, rq):
    """Take the pages of this prompt that a walk from the start can still reach."""
    w = kv.w
    prev = 0
    j = 0
    while (j + 1) * w <= len(rq.prompt):
        pid = find(kv, prev, tuple(rq.prompt[j * w:(j + 1) * w]))
        if not pid:
            break
        pool.hold(kv, pid)
        rq.pg[j] = pid
        prev = pid
        j += 1
    return j
PYEOF

cat > /app/kv/live.py <<'PYEOF'
from kv import pool


def holds(kv, rq, i):
    hit = pool.look(kv, "at %s %d" % (rq.name, i))
    if not hit:
        return 0
    kv.out[:] = hit[0][:-1]
    return hit[1]
PYEOF

cat > /app/kv/fill.py <<'PYEOF'
"""Filling a prompt: the walk once, then written tokens a page at a time.

A prompt is taken up as soon as a step reaches it with budget left, and what the walk
reuses costs no budget, so the reuse all happens in that one step.
What is left is written in chunks that end on a page boundary; a budget that cannot reach
the next boundary writes nothing at all, and since nothing jumps the queue that ends the
fill phase. The release of the middle happens when the prompt is complete, not before:
until then the request holds every page of it.
"""
from kv import keep, live, put


def settle(kv, rq):
    live.trim(kv, rq)
    if kv.wait and kv.wait[0] == rq.name:
        kv.wait.popleft()
    else:
        kv.wait.remove(rq.name)
    kv.on.append(rq.name)


def feed(kv, rq, b):
    new = not rq.got
    got = 0
    if new:
        got = keep.walk(kv, rq) * kv.w
        rq.fed = got
        rq.got = True
        rq.up = live.sink(kv)
    left = len(rq.prompt) - rq.fed
    if left == 0:
        kv.say("fill", rq.name, got, 0)
        settle(kv, rq)
        return 0, True, True
    if left <= b:
        take = left
    else:
        take = (rq.fed + b) // kv.w * kv.w - rq.fed
    if take <= 0:
        if new:
            kv.say("fill", rq.name, got, 0)
        return 0, True, False
    done = 0
    while done < take:
        if not put.write(kv, rq, rq.prompt[rq.fed]):
            if new or done:
                kv.say("fill", rq.name, got, done)
            return 0, False, False
        rq.fed += 1
        done += 1
    kv.say("fill", rq.name, got, done)
    if rq.fed == len(rq.prompt):
        settle(kv, rq)
    return done, True, True
PYEOF

cat > /app/kv/turn.py <<'PYEOF'
from kv import pool


def step(kv):
    hit = pool.look(kv, "step")
    if hit:
        kv.out[:] = hit[0]


def kill(kv, name):
    rq = kv.rq.pop(name, None)
    if rq is not None:
        if name in kv.on:
            kv.on.remove(name)
        if name in kv.wait:
            kv.wait.remove(name)
    hit = pool.look(kv, "stop %s" % name)
    if hit:
        kv.out[:] = hit[0]
PYEOF

cat > /app/kv/put.py <<'PYEOF'
"""Writing one token, and what happens when a page completes.

A page takes its place under the page before it as soon as it is made, but it cannot be
reused while it is still being written. The moment it is full its tokens are known, so it
either becomes reusable or finds that the same tokens already sit below the same page - in
which case the request hands its own page straight back to the pool and takes the one that
is already there.
"""
from kv import keep, pool, store


def write(kv, rq, token):
    w = kv.w
    n = rq.len()
    j = n // w
    off = n - j * w
    if off == 0:
        pid = pool.grab(kv)
        if not pid:
            return False
        pg = store.Pg(rq.pg[j - 1] if j else 0, w)
        kv.pg[pid] = pg
        kv.ref[pid] = 1
        keep.join(kv, pid, pg.prev)
        rq.pg[j] = pid
    else:
        pid = rq.pg[j]
        pg = kv.pg[pid]
    pg.tokens[off] = token
    pg.n = off + 1
    if pg.n == w:
        had = keep.find(kv, pg.prev, tuple(pg.tokens))
        if had:
            pool.loose(kv, pid)
            pool.hold(kv, had)
            rq.pg[j] = had
        else:
            keep.add(kv, pid)
    return True
PYEOF
