import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header, get_header_for_patch
from step import project_steps, cluster_steps
from common import commonFunction
from math import ceil
from common.getConfig import get_apiserver

env_url = get_apiserver()


@allure.step('创建应用模板')
def step_create_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用模版名称
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps'
    data = {"version_type": "helm",
            "name": app_name,
            "version_package": "H4sIFAAAAAAA/ykAK2FIUjBjSE02THk5NWIzVjBkUzVpWlM5Nk9WVjZNV2xqYW5keVRRbz1IZWxtAOx9f3PbNrbo/q1Pca7SncR9EiU7zo+rTmee13Z3/W7qeGynfZ1Op4ZISMKaBFgAtK3r+H32N+cAIEFKspO2SW93zT8SiwQODg7ObxyCci7kzWh/wbRNlqzI//IJrvF4PH65u0v/j8fj7v/b+Pf27vj5y/Huy5fbO38Zb+88H7/4C4w/BTLdqzKW6b+Mf/NY3cn9SS4mpbLMCiXNpAfAyjK5rKbclAuueSLUKGWWz5VeTuCY22ulL4Wc91gpvuPaCCUncLXdY2VZ/9xOtl8n417GTapFaekeMRkIA0zCP87PT4DJDDS/4tpwKLW6WYLh+orrATAomMi7N2UGrAcw55JrkcL5/sno3cFJp5XSYi4ky/MlXGthLZcwXcLRXGk4WxrFr5KeSBGdhbWlmYxGVZkrliXX4lIUPBMsUXo+wl8l/hqlqiiUNCO7qIrpKB2lL0bHOJGfczVXibmaj16Mx+XNsH0zKeW8VzAhLROSazPpDYHjnCbQEPZ/LyspZsskVUUPQLKCT+C/qik/o6c9d4Oo1jOq0iknMAHvubCLaoqdRw3I0YLnxTBFQTYjqzkfFcxYrkdGpyPEZ+TgXTUL9Tx50XPyf8XyiptPpQAekP+dl89fdeX/xcvdR/n/HJfmZS5Stq8qaSew3euJgs05qoKFLfIJ3N71AJ6A5qUywpIecHyEdy2bT+iPssrzE5WLdDmBo9mxsieaGy4tMje2xlawFkgEBjaDIYl4e8W1FhmfQL/fm1V5vnKzh6pApIS+kyEUmR6AXZZ8Avt5hRJxdNIDKJW2E3g97vWEnGtuSPtxyaY5zyYwY7nhqA4j7ehIgfii0GnJLTeoIH3/JM2ZMe2JtRva3AxZilj1ra54H7FgdkEjD2GEJFfG+p8EJslVynLEPzcT+PEnojUMwfBUc3vcaImhzY17GAGhX21IPX5jNftO5VXBHcQn2IIA0aMeduJFaZcHQtOU4y7fIpes7WeoY4HPT5hdTGBUGT0yC6a50zsjZCdqpDnL3sp8OQGkgod/JIXdV7XObI+QqaFRBbcLND0IwvEoTCuznKqb5tbJJv7BFqjOmcwm8OPTTD0dwNMa5tOfej3ESkhuzIlWU2KgkubRH+E6CSmsYPkBz9nyjKdKZmYCL7AR10Jl9a3nPYAZE3ml+flCc7NQeTaBl71cXPHfAXhP82AOgmDmohD1cqdlNYHt8bhwPwtekKxt77z+Vngx/qXi5sPa91IlZ2JeaeL/b0TOadAnXqQTfDyB90O8g2IGt0Rmb47DL4BcGDTFr8df1XdUSjBh1LQC0ErZ9WxTd7xzf9B/gTP3u1iagGbGZ6zKbQvRz4NeT6qMn/Gcp1Z5KbIq5zpokh9/6vXYbIYLv/SPw6p0VNAn1/8t+2/SBS9Y8k+j5O85xgP2f/xqZ7tj/3fHOzuP9v9zXLc9gP4XbuH7E+gHHxN5YOj5Ad3iTLOZHY5fjdy9J/0BdkS7ir3U9J88te5eqVXJtRXc9CdwS5awH3sZ9d2ov5CWz7kmAO6BsDk9OXU9Dbi+dYOZ0kXfmZD6XiGkKCq8vU237tyTvrfQ6waOEG+Pe+T73DvgmqnSfS/ErZvRoFOlcs5kDbs98qHv3HoajV7fvuvF/+O/d727j9UYTv4tL8qcWW5Gx2/PD88Se2N/Rx57yP9/NX6xKv+P/v9nubYT+Du3YBccY38UNTJ9707fYPCsKymFnONjw4MHZSa929shiBkk3zm7EVxgz/dwd0ctNJNzDl+gQwqTr1dak6OKbQGi1t1W5CK7Vqibbm9x4JVWNsc25vYWuMTxJ6PR7a0f+u7u9haSZiDXotf9MzccQafOCzXQP1YZP1Ha9mvMfXiRoCA7ePwGAwk4fntw+PPJ29Pzr794hk5/anOYcwvDIXqwpmQpB0TilOecGZ4c13fv7mCoALUtTvTr/m1iSp4mCNX8OP4pkR6Juz740Q1CEjLNq4xD3/liIRrq0zy3OogdnXTQQqDmVyEnLC8IL2OZrUzCsgzpz+me/3HXJwTShaIVm4xGX3g0Jl/UhNpA8zeKZX9jOZMp1/fRHQBQU03gyELBlmDZJQcGM34NhZCV5QZmShNbxyDh6ASsgikHdsVEjtyaRGoWflAVpEzCNbPpgnq7eYKaxeLwNCamuUpheP3gojxtFuXs8PS7o/0160KgPmRVHhqstWxPb8Nq5REpgujgwony7unKmjVYThCPzlLQRDaKTh1pf4DsnLw9+Pl479vDDi1KlX0oi+bQD3nLJtrGjl+v0qmh0WC1j5DGInG+7o4Fd3f9jaJQcMsyZhnBjpi//50wwgZ6bu+8SsbJONmevB6/HiMXVobDUlU6VrwYDwYqIHWGM6Wvmc7gi0AmwO6T1+NYf/0G/d+1/z8veF5ybRJb/m6pwIfs/3i7m//bfbW9/Wj/P8d1ezv6Eq5EMQHDLcxEzlFAvy6QLOmCT+DLEUn56Mve4U3JZEZaETkddSL+TSnnpOfbDTHsFrIjb8PmGYbkkLgNJxKtoCDibB68R1dXpvDyOf0pirNqNhM30B82wJD58W+H3b7mzKINCGOgRlzCLxXLxUzwDKWM8E5633MHndpbHAPnYGDKU4ZCaVTBKR3vNIOb7UzwPDPANHc5F56hDNuFMPBsuiRKHByfYVu0EGjEt5Le0Qy0UyMOSK0hiWjunrBwLfIcjVJlEE+DhqzKc4/tBsI2Cj/QI3LIutnRus3GBh9EcNTz4ccXhPzk6w9f0wjPmg4OSlvX1ri27n40gqUW0s6g/1cz/Kvpd6C5cT+Gyzb93eK+aFlRVPxeCy4pLa3nE9cqZ1Oeb1xeatPfOJmY1u5vvwEH7wGDbTSN/f/Vh/7P/Y+a5R+tjh6vz3x17X9aDCmtOnTZ399lT/Ch/N/ui679f7m78+rR/n+Oq2M4NqTU0cns7PlfCplNwDX9lpW94AU3e2+3txD4an2U0uY034/c+slGb7/nxogSBpd8OYAvrlge5xjumQcgbOwFd3e0LYA/sft7EDLj0sLumuzAv6p+XCP/BRPSL8rvUxHwkPw/f9XN/70c7z7m/z7L1ZH/lT2/TyT5EY99lNyvbD7iUGV+D/5JJNf/8tL88VdX/jNe5mpZcPk7lgM+IP+vnu929/9e7O6OH+X/c1yxbLOyNKNawA9qTlgv4fcmIHvg4hvjCnvWp+fWgWmBAFjwvEjMYkTh0Lr2Pk6qO2xO6q3qls19CibZnGfD6bLd68wlMbEjRvg4Ob+1aVxDr4bi/U43ignVADRiwWy6eBMR6DeQ6NfMOci7xyZaXiqAaCH2m1D7dQsSaIuXaFcG+bvdDaiCzXmysEWeNEVmDRahkChV5XJIhUgBO19JFC3dJlCT21tIFcu5Sfm6xpbNoU861Pbj+a8UJj0Ap6mBg35cw9QCGmqZ6htDMIvoxzCNfqQlDDVQqcroS3CFK20qXMXVXVHPUEMXNW0Xea2B1ZQoRX3iuqMIUqg3GlN5UnP5uqQiWmzvizc3roVdtN39dg1Zu7VVP7AiJ2dAem/gZbuFH6AXCNzluIYeyCxR/iValpqf+isM5eTjQznKtUaWehZlflheCsnr7M9eXXW9BXd3/S4WHZ5bN0DEa61Z0O5je62G7YLK1moFWp0or6M3bRa1+5VaWZWqfALn+yfRs5ViuebC0f/O7aQLibgxGrgFgraQ1wz/MdiurdHbOOCa1l2Andq+zbjH7dpAVksWP55QbRifg1KdEX8TqbrYb6bVurLMzYC6bbt0X6Ph2mqmButbRmpne6cNbb3uXbFwawOzpnUQz3Zc1Vyx0uY29dWLTSzVamyqqWu69vmKNl6D7b3ply7O3SzQQ1hjyyT7SIwaC7seiY6R+4Ba5g8Yf9VGxXXUq+3XWKnt8Wqztqm68tXcvXsm1Kro/lj+uo+30pAFiFn31yUB1lLyY/nqfp76TdiuA/mBnokvuP+VLskGyHGNcdOsVXnce4C5Xm8cb2W0UK4cRR2hgPmDR3lojKhGuhkmLpz+NSP90QH2//Crm/8JBXW/56tgD9Z/7K7Uf77aefmY//kc1wOVnPVuPyrDY7/jf0/mp27vAZ1Q9eaa4k9X1jnsZJf5jeUS/zSjq+0ptywko3w59vpMVIPcv0PiaY3iDESNXldzLTtv925UnLsr1bEuBbOBO1y1rX8vrVW+u7Elmub6zbSAie8TFQIHK04Vu+/hl0pZfo9RjF+Ewy7N7/vKfQF0lfMHMG8h5XCfbECLKvxq5Ot3+mJj5fcqW1LR8UOb2KwbukxZesnjbE+YPPHE8QYxWNPUBeidEL5FmPUE+6OV1OP1ya6u/Q+h/We0/9vPt7vnP+y+Gj/a/89yrd3b9dbmcd/nnn0f90r5mqRYU+AepVGHH5pEs0zPuV1R1OtypU02ugNRtmyAt+H8l/WYRq+5tILIjcnc8HCDWW5vdP1qBvjY9fyj5ejPenX1P72ITP8OUyUlT9F5/I3W4CH9v73T1f+vXuw8f9T/n+PqePi0/PF7fGvtw4nK1tiG/kPGYdhhq/6/vrVYE4L1A7YLpS77EyCimCpNMb4N1qW7/xjymtdzbsPGePsQDHczOuQCmz79KSTr9NxMAH58+tAa3fOuFwHTHOXFho3FY37F9WOo8Oe9nP5PkCfFXCrNP8EYD9V/vth5uXL+02P+7/NcT+CEWcu1NGAVOBaA6wWXMK1Engk5h5Kll2zOTdJ7AucLYcBUJbm2YBY8z2Geq6mraBJyPgDNc2bFFaeERnSfyaz3BCSfuzfMn5Waz8QNz1wq6z+2Engr8yUoST0RJSi5hlxInvSSg7Ofz6zSvPcE9ulcNvhu/wwyoU0vmQs7on8d+r1k+t96RP+GG4v5CP8JP82VHDWApiy9rEp69830vkzMddn7Mpmyy96XiS3K3pf/r/cEvmNaqMrA0cGh6SWlVv/kqe0lIuNs5Npp9c9ecmVSlfHRn0gLOvl/c7R/eHx2+InGuF/+d15uP+/m/7d3H89//DwXPHTtlSxdcHgjUi4N793TMryBtpOMB/B/mKyYXsLOeLy7sZN/Nfr6+jphNAwdNZO7ocyIdrjPD0+/PYO94wPYf3t8cHR+9Pb4DL55ewrvzg4HcHp4cvr24N0+3h5Qq4Ojs/PTo7+9wzsEYDuBA05bleiDJWHbvO9n1AezYHkOBWeS3s6zXBeGXt9LlcxcLzpMoDIctVupVVaR/xpOaMG2mTBWi2ll/ft+7m0+euXvzHm7BrbBLrSq5gv4T/fyrDCQqbSiausOXkqvIJaqcqnFfGFBXUuuQWng0gq7BFbZhdLiv2m8kEhY08MumAVhYK6ZtP5cj7CyEQJ8znI4JNArSFQSJ+hf/WUpQQlYyAxYHooOlF1wj6Dgxg2NXq1W+YDeovU/ckJ6gLPBu5XMuAZ39GZUi6dV7uwEwXEDJvCNP+KhrHSpDDcNVesFr8/q8VD6NBUDz8SW66quuR6gIeGpRSSEdH8P0B6694HtIvC9e0QU0ODcf1w8HNdU6cIjNkADStOfLh32jGDHlLkWyE1KwzMhttzymIUoEdJMzOwSbV+KoJ+9GP91i4ZDy+wIHwBVFoMWMtJUnmICRLEFUy75TKSC5W3oEZ7Nkv+gqj48U5r+0v2teNWZJJpciaxCWBpi/vAA+A3XqTDkLXBdCEN7eI7Pwnuvwqyy2hmVR/VRvIoup6F/wLXmmXs6I4pf4hCFysTMH5hgwgK7qAYfTysLUtn4NW2jZvYa2cvVYwFa6UEtewQo7ChRg0GQ/6bQxPkHDepv3clRK6gzuXT3NDdVTvIx06qAgqcLJoU7z5EEVDNpsCULDEV3cv9zBgwceQjcoD3BOlHXmmaqilKgQLljrfw06dRchk1aE461V6qkf1eZ3EAnu3QmLuU5o2l/r/TlilK4VvqSMCY9hJzWiICQYRq1ADjS+WkVLItOY/HyH+mlAWpTZMCUeVZitV4I2k0qi/F2UG8+wM1wbFQrlo4y8O/rO2w9iGdMAr9hRZlz7FhqdSV8R2y5V5ZcZuIGpjxX11sNFQ64FlfOy0WCmH6XA3CM9TTws/eQHA0C4lNmcPEkiWKGYyD3a1U4XYVD0XKhLFwvhDuiJohgJqzSKO6aXwlaykGcfBgAz9lU6fBL6bDMsTR5YGjlqOp84I4juF6onISiPmR5zZqv6uOgp2Yt8R9Al3yeesjNITlxTfeJMJoXTNTyyUumiVOQLjSNgmueLzFQuCTCTYUkPpGs4Fth0YW0XM9YSkZiENnImqgrSCF1uJo1q76Pqtzb+LUr3pWBWmSj8WoChsMBvC2t8UBgrTUhHs68J1JXRTnaUC+lNyI/iITCotZXdEB2IGY1LYT1yiP4HcRdhDmh50WBBgrnF7TdirDKZO7utRaxo4JamYZHfp/yBctnoGabnZcPs/bQr+cUCuKdva/VspoB7VBoJUU6wFWYspz4KBwajs5HJcNJaP4Y45rovCEU0smaRliI/mZwrymK8nTNGEpGONEB6Ng5F8aaQWyyalfILI3lhYlVuDCm4mhCUrKRvoVbfrR8PlkZfK2Y6INIjbS4IKI20i0TJq0MWXkasSB96d3I70njNaaJ3wQitOca+DFV0pQirVRl8iUUTF+i6tONdxRcLm7EXJLuF5LWiAi7lhNRWfWPlQUGsawm/VUR7vjX9bSDBD7o8sQERP1YdAaFBTMw5VyC5iknTT5dtsZphNDwXyoubY7DpkqXyplrdHgj8XOKaCeBv6NbhcPu19MPnhWcVc64el5dG8xEYhZrZc7SBUQEAlQh06Xz4sgv+EFVwNDDK7mtWB7Y71rpPLsW6GtIJYe08kZc0U86kX6OgZNastwuhzPN+QCE1vxKpajIV6y5j/9wwBBt8QG6gyXy8Yqma9R5WU1zkeZLZNQyZ8tBc6fk2plaQ3e8YxHHbbGbX+ticpZXRlxjzkm3uAV6Hi3QCUOl+y+wOs/4TcpLiwJmbBBGQtC4gGgLSjfXaPUKdskHsGBXnLy8gBDF0Wo2Qz9PgeF5PvD/iqJU2rqFqfWAd5S9V0hqJswMSeDWKIxKR6mhaZD50lEZdZdHLc2ZKIxvG01uunRAYurWelPylBvDtCDpnGkh5/VJPiLYvljwn5ktYLmS3FvEVBVTIWuvnrp1O4QJuQjXW1urvJPXRs4PcY1LEWxdAkczXP86FjJWWOTpelGs8HlXNmf4mJScD9yfNQar9q21MmZIBMNppKpC/8n9FhIY5OzaVMLiVHM+d0aA2Rr5xifoaMX7FBzZBIe48aF2AydtFmcZphXWoyBP1S64c8XanBhcphCMekkJgUYjY97kBa/KWQcUUVy9wCvMBIctY7Zmvpq6wlCcmDlVsJvAKY8zQwkNXbBlo9m6WihVpQi+TUsf3ePl0ZKg28gzURUDx0fo0Qi7ULVFbofNzoRv0GSDJhQigjSsVXB/WuxM5bm6dvY96K5Jr46rttxMK2Nhjvgiei7e0DwVpeCotGLXt44O8VqZKCP70I0kviIzGsacRmO6xE3jSmMcRW+KUFJHIwtpVQiJfOKix/jNI1RxNUvTmaALRmJPE0c47ZHTaGTNLRNyEPzmKISn6EAuVyYXDVwP2DDEACWssY4Dz90DVIsZR79pEDkTxKK2ETc/N5eCWINPV6W2PTenPQMMQi5T5NCWXOM0kZxO4rRtDBd4D7470TbRsi1UWvX6+8APl7p//Pb8aP+wD5bfuDMJUez8GOhyR+PE0hWpgDWSskJZWq8IVAg9Gb1ZSTFmw3R8LVnDNn1Mfq/USDO4idAUBh9C1wjMegqvpSsxG7OQc2YwnIqz9L5LI610NpyZBDRZwLGhdUOhFleZe3H4KlbmLSaL5bqdgAIxa/QMmsx5YwFX4Ss9WKUyC75elOUKpzGuUmnWkRRyIK64dotlF0JnQ5zksl4bqXRBX5RiZcmZTuB84aIw1F+rZI7Wm5wHF0rXST6WR8EreihtdLxskcZatnLztdlgWYZ/a4x3Yo6MoATUPYU+RBIGjvpGZC3WoXiKSRyUy6wqgtva4pigWFz8F5azq9OIwCGJwfL1wkTZKphy5wfoqst/jjCb9i3WkqiJKshtpWS9cwA6ia9oKRCIn0eMstKQCfRaW17uGg++Se2t2TJyYKK9IjVbg82gEZsZBYvLDaFInJ2rRYng4dBRNq9BYGW3qmWFa687VYVzpZGPWmmZOlLpRAKtBXlBwY7fCXCxauMFmgTeyZwbQ4vGb8pcpALDX4IYbZDU+Y1l14uMkllRGmtj6qrx9HHEbiLHuXrTOPv8MaGZd7MIzYhhHAjnumZh99H1P1YWO9W7N2RfpsoFZfRNIgrv0IwQaqYquTY8424jCMUgWhI/kPMuXILU8iYkmmvuGH/pJYQiMn7D00jFk+KtCaL5nGm3r9SNPfxewMsEzoMDYhJXFxL86EyR5rTO5Y52hMKp14Q09g7bGKzgJvJozCC8sQL+p9Lgedg1DkwbMB40WScfpmr+SyX87hEadKOoqNEtaWWsKpheEjZCgvta4dQvRR10iLlYzc8GaQrr5q3BGhPgKPUqgQNhKHTiGlt9zzTSZVkLQY3qdBnOAkdMc3bdqAFaRQpemizYoFkwL/umQfUZ4spZuuiGqHFrYU17cbdA0Y5ff+8Mjs768Le9s6OzQNzvj87/8fbdOXy/d3q6d3x+dHgGb0/jbfm338De8Q/wX0fHBwPgwu0A35QaJ1nPRJBeyaI0aSNBlCdlQU8t4dqRigIivapi1QzOj87fHA7g+O3x8Oj4m9Oj478ffnt4fD6Abw9P9/+xd3y+97ejN0fnPxALfXN0fnx45soH9jyMk73T86P9d2/2TuHk3enJ27NDZ23dbmHOc4zVTKmkEbTrQDszLipsswsrS61KLdA9pwnPoKJcKfFfo3GjfKnLNhpT0XnBQaS1MKTZjUpFHSY7pe73WSkbG2+0rgazjvdeJ/CmJil2eiPYVOS0eX6Elhf4FfIu4uFgSAU5JTvtgiu9jFItYSfLKm3jlIHk81zMuUz51qDe7R60Url15udBfn/mHAUDGc/FlBw6Qm6ulTH1vkUY0gJLraHd8fXy4bRny3woDdOwZLmggX1GgJaWFWzezuFj71AS0BQHmJKnokmyCZmKDB1bt5WADozL6QqWB6BBQ6cLhiTiGph2e+ZoxWtbbarcdgNdomZV65jK3RHSL2akV+OMwbN798QDVjjtXDmGnSuVXYs8zh1egrGqLNmcD8gnqBBxf0CKq4LIZ5VsnBsygmsqQVJVFMi8MT3cwNxsDYgP0UHvJuI8jDqZzrIrQZukM1++YYzwRAjFDR68k4D/TGAvRZuAVAiaF0feawx1JBTfL9B1b4trd7Pw3u224IWmC6VcFpQyna3Ndsq50tdKSJ8MgBGGTKbcTaJ0aVCv/ZbEd7yQwtbyWO/e5gF3UNPcZ6HIbxmh2kHP12210FfubIivhGlt9/AE/qGuOX1FF4OqmmBEzwhwMz+qaJF5tBtS+9x+W4SSuP42KtJGjRK+5Ok0uyiNRm8yRREb+Jwwxkxi5vQzCryTd6LNrKZNxmdcZq4Hnd6zmjpnuiBNFJzrmoqNOFdaN7tlPnPMjOEaxccnUQereePp0jsbzYTcNz5qmtbO/HXEjZHbWOPiGPjw+ADt6royOHq+d3JyeHxw9H8nuISULSjLfOnLF+LSPXxGqFzXe0kAcP6BHQa+jKKdTQhutRI51+7wFBfNDZpI3n84gcs0V/4Q/Klm6SW3Bvo//tRvgpScpcHaLQMzkVb1UV8USSfw7EDJp3W9QCSjAfh/bAFF6xSmmoWq8gxd/BoPHx1EZjvam0VZMUtp2U29EUpBvUMgge85sNwo0Ny19nnSoMWpreMbY5rvAUQfxSYL7rdWp7wpWaEd0oCJwY59OgGOZ4A6uI+2or3z6YtfEE3OjKj34z3lwr5rnZ5pkhxMpwtxFTRls5n443K5XP4EP4avfHR2WX+i5p5JsihmarPPIC4IhWfYoK653PoKQYR4BBWBM18+fR7ceCF9GEqqseao2sWJon41pWwZa6XsAiMzG9j9oZJTXwg93EnG1OVDPPRNvoevOevFWcoWvQJ6wrQabPLAf6P7HRxvItsZ5y0UApOTWzMTKeRMzis25zBXV1zLbmWfz5Y0/rpZnVfyJyqD/7e9XP3/6eHewbeHSZF9kjEeeP/n+cudlfr/ly8e3//5LNcTOKYPlveePIHzN18dnH7V611cXKDLqHLeW/C8oO1kjKMuDR3Z5g7Bw1bU68g9RW+gd67qxs2Hbmq93foU0kWxHPobF5PNY7ovwEHTeB0WLilPbz6CO8DcGUlq4rFwhjX+rFPqPlIXHIHwHaNW1W+d8I8KgX3Fg6vPclEI06zglutQ586kT2NTN55BVmnnwdCsHGii3jsp2vSrwo1RxnPuylJaxILmiPY1dPOdmvarFNK8UFfcQFilmCSqKJWkvdlu/qFZT0flnDpEy+rm0zqcz43b7D1ZZzVrutV0xdsREb35jpfPf3lM6Hqd/Dere72T0BHew0HkYeEvatobDofwHup/exdrD3m+gPe02vSQIgcKgdC+pc3uMX0/HLmJ5GbgSzTom+GUSryg0yEv4u2w+mXeryjCdSaWU4TSPt7afQiMPBg3nrOpAaRVcLH2LMoLHPjYUauG9R6kkrw1V8vmYZKWzQOZP2a+66A2pwgH4HgHSnew8G8fpHt0cnud1GzNzC+oz0UbwvrZu84O1nu42E62XyZjf9RyB8AHTbQDLz7C+6J3ER+9EYCEVDfeGwTdcVF/QvNiABfhjA7sEj1p4JX+YQyPXtuO2LBUWZtIr8cRBBkNcTSDDqbCREgMnKdOAtj+dl1YuPjUSwR4iL/DSaXwHn78ybehk1BXGtLZq+uat4/4bjqgFEXvzPsuK2eaYod9yv2vebeDcjXhW3UXa0/JvWhPcPUg0nsHIE4vK1tLdfdI2xr8H+0UPF6P1+P1b3H9/wAAAP//g54NlACQAAA="
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的应用模版')
def step_get_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用名称
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('部署应用')
def step_deploy_template(ws_name, project_name, app_id, name, version_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_id: 应用id
    :param name: 部署应用的名称
    :param version_id: 应用的版本号
    :return:
    """
    if commonFunction.check_multi_cluster() is False:
        url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + \
              '/clusters/default/namespaces/' + project_name + '/applications'
    else:
        # 获取host 集群的名称
        host_name = project_steps.step_get_host_name()
        url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + \
              '/clusters/' + host_name + '/namespaces/' + project_name + '/applications'

    data = {"app_id": app_id,
            "name": name,
            "version_id": version_id,
            "conf": "replicaCount: 1\nimage:\n  html: {}\n  nginx:\n    repository: nginx\n    pullPolicy: IfNotPresent\nnameOverride: ''\nfullnameOverride: ''\nservice:\n  name: http\n  type: ClusterIP\n  port: 80\ningress:\n  enabled: false\n  annotations: {}\n  paths:\n    - /\n  hosts:\n    - nginx.local\n  tls: []\nextraVolumes: []\nextraVolumeMounts: []\nextraInitContainers: []\nreadinessProbe:\n  path: /\n  initialDelaySeconds: 5\n  periodSeconds: 3\n  failureThreshold: 6\nlivenessProbe:\n  path: /\n  initialDelaySeconds: 5\n  periodSeconds: 3\nresources: {}\nconfigurationFile: {}\nextraConfigurationFiles: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\ntests:\n  enabled: false\n",
            }

    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用状态')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看指定应用')
def step_get_app(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除部署的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param cluster_id: 集群id
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications/' + cluster_id

    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('应用模板提交审核')
def step_app_template_submit(app_id, version_id, version, update_log):
    """
    :param app_id: 应用的id
    :param version_id: 应用的版本id
    :param version: 部署时应用的版本名称
    :param update_log: 部署时应用的更新日志
    :return:
    """
    url1 = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/'
    url2 = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data1 = {"name": version,
             "description": update_log}
    data2 = {"action": "submit"}
    requests.patch(url1, headers=get_header_for_patch(), data=json.dumps(data1))
    response = requests.post(url2, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('应用模板撤销审核')
def step_app_template_submit_cancle(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "cancel"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--通过')
def step_app_pass(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "pass"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--不通过')
def step_app_reject(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "reject", "message": "test-reject"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('发布应用商店')
def step_release(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "release"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('下架应用')
def step_suspend_app(app_id):
    """
    :param app_id: 应用id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/action'
    data = {"action": "suspend"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('重新上架')
def step_app_recover(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "recover"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用审核记录')
def step_audit_records(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/audits?'
    response = requests.get(url, get_header())
    return response


@allure.step('添加版本')
def step_add_version(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    # 获取应用的app_id和version_id
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions'
    data = {"type": "helm",
            "package": "H4sIFAAAAAAA/ykAK2FIUjBjSE02THk5NWIzVjBkUzVpWlM5Nk9WVjZNV2xqYW5keVRRbz1IZWxtAOw7W2/buNJ91q8YGLvA7n6wLOfi5hOwD1nH7QabpD5WesNiYdDS2OYpRSki5cZN+98PSF0sOVIsp95kD47noVapEefGuXDISBSShOFBpz8nkTSXxGcvdg2WZVkvj4/1r2VZ679W9/jgRfewd3hk9XoHvYMXVvfg5dHRC7B2zkkFxEKS6IX13bTWhfsvARLSdxgJGnAbFl2DhGHhv6ZleCjciIZSj2SLBebIfHDVioECgsGJjyssY5HPZJn/bzy3pHuogtz/F4TFKP6WALDJ/18eW2v+f3hg9fb+/xRAplPKqVzacPfNICEVGC0wsmEuZSjsTudTPMGIo0RhejglMZOmWLj20dGhgf7N7annRSjE9TJEG2iox/oBn9KZbQAMLv/1YXx5enX6enA5uLoejy/OnevB1WA0Hv9+fT20oXVinVgt/dUFdTkKdNCNUF7pQMJjxgzqkxnaoFA66h+bEbVmk/FhzNgwYNRd2nA+vQrkMEKBXBqUzxRfignCeSCJik9CCwmAnEwYejZMCRNoAMwDITVuOwlqbbwlfsjQZIFLmAEQEjm3oWMASCZs+PMvHepESFy0IdWLwQMPHWToyiDSlEIV/4RE7qJmxHVRiMvAQxtGSLz3EZX4hrtYxZKgX9CGA+uSGhGGjLpE2HBoRCiCOHIxEUUZiyaTS22BPouFxOh8aMiAYZRJ/edftdE393+JfqhV23EkkTiNmYM7qgce9v9u99g6XvP/XvfY2vv/U0Ax/5MwFJ1F1/hEuWdDYRkYPkriEUnUSkuS/N0dUO6y2ENoKbc0pzFj6lULTPj2LcVLPeTuDswRMiQCzatsOMFiZIJM+x4o+mYh3tCgU0OrRAd0NWKKeUf7bgW6Hi/g36dDuZCEV7Fa/41POJmh154sy185iVOqD0WIrhIt9dOrJpprz5F4DIUwAO7u2kCnQLgH5rskPxdiipkGDfiJB7Ia4ZYKSfmszwj1f05EWQQs9lGPXGcun6i/DUUzJ5AYQLHZVi9K45uNm0DRxAk81tAJbGvuOpqbjV73ZQPT5x8Xsk8+mNq1ymRCBhGZKfsIUWYjMZw5QUnW2Em/abvqo4SjTTN/hZs4kCVOFVPIBFZSJSycbyCbpcHSfNxbTZd5Q6qYPBuWlka7jv0VfhXzq7y4mivCmxjTxJ5DynS9luiXNQIlOeLQIxIdGRGJs2Uyc5J6RwFjlM/eagRDUc+ydoFSNphMJrJiQU/jE+nOL0q+8ng/2X61Z/k/ZWYtEqz78Pd48GM8sbh2kiWZM5M6U20MTINkzkC7NqihH8rlGY3SMrHkFDXuWoqwTWjkH8t3q0BcjgyfqZxvQ0yBq4by/CJDBib8cM+7i95YOVCQsrImhxoRGXWR67o19TL9RdHxRKGuLzhENZV6JtNMeuq6QczT6RrUIikHcUTlsh9wibcF5qbidRTEoQ1dy7LSUTfgklCOUWHNFyUuSJZuUApC6ZGSee5tVtaxV+/Kdg2DSK7Fx5y1YZCmv6Iyk82XqXdeq93WdX84Hg8+XA9GV6cX8DWL1dA9OTksE3zc/I5zUTn/yXfNX79zLJKwTqxdiPDeqZbA2o2G3ju18x89fv6zU+f3396cjs4eUFD3vgjIF6+iwC8lxoTulM4uSTjCafkdQMO6v418AWVK5dWbzKKZvzq9HJSo6BZUZQ6Aujn6F2+dayX0HyfOeHw6HO521rNzp//m3WD0sWrGTyeiIV/OYPTuvD94iLemW4JGWjhXBAejOjWkiynv9jRXsBLAGZ72G2n43kbgYa7PzkYDxxlffxzWzl7wgkLjqUwiTWN4A7X4rXkgZKLeptw5b1+9Ov9QxZdYuKabtF3ydlGRl6x6wJt6fjwudsFKGHgPs1LMpFCumlXVEHwkPivUqulL+AqUe8gldA+qNgeXKhWLKje/X/4o8BX+UHfUWp0glLqt11FoHZ+joKRV4nubouQe8fXCpJ4+Slc/mIy6rRK+iCcpdvX7CIn3hrOlDTKKscx7hcqJRzkKMYyCCZaj7FzK8HW5bFKQNh+FJDIW6+90hlA5sPSCciopYWfIyNJBN+CesOG4hBJiRANv7eW98rPY01wJUup0lkrMbA3BV+DpojmpLefuUcua0YV9TNaebkxlE41CY3RFptgtfQSl527ifQdU9H/Hc2Rq22HKcDdHQRvOfw6s7tFa//f48HB//vMkcHfX+QUW1LdBoIQpZSiXIf7qK7W4c7Thl863b4bCMga3IeEeyDnqCAvBVD/rdptppHhtVXdSXt7+t1evdElqJpcNdPDOIw3x8c0Co4jqDo+MYu5C71A/Ut+Jp1N6C632ajLleuo5Ya4fIZEIJKehSqgl3MSE0SlFD0gYarZN4z0ms2t8qWgoEQRM0CWxQBCBj/BH3qBIhJ1SZJ4AEiEw6lOJHsgA5JwK+Gmy1Io4u3IULuUz3a742TTOpxAlBVEySVrYi/ToXI9RCZ8pYzBBiIXiUwDRzKfcVut1VSBm6ihkyexlrs4Mpxahkb5VIZP95wfNu/1rc5MW+MzVkMxSLstzXkujWzMYRpTLKbR+FO0fRWtttoTuNous7rm0+ApWVY6SXn9QFtWWTZdJgqUbanXWTTvYdbIUVZ08p0c48FW3HVXZ3fq/FrTGra2EfO5YtIenh4r8n7QBfBLu6jLIpvsfvW5vPf/3jrv7/P8UsHb/Kzn67WeNoO0PftvIF/vDX/VhprbiNuJeG6+wrzh4lo1Ehf9HE+Lu9B7YBv/vHh511/z/qNfd+/+TQKX/O6VTlntBYLNjN7sj0m63U4KjgKFRZEWvQRLLeRDRL3pjbn460Z636E5Qku7fxlQUMxS20QYSUn0ulF4Ma7WMtWNmXTiFAeVS94EXGE2EDfrFDKX+/UykO9dPjAq5JvBvlHuUz/4hcot48m90s2twlesAmp4C5JibmIsChulhQ2EhNKeS2egBxT23g/3DoSL+p2esu0sBG+J/r1fR/zk+2Mf/p4CH4v/+2t/3XftLLgYVDq4yz5LJqZXKFfkBf3Zs4d/IJNKGuz3eD6NABm7AbLjuD5N7SySaodzpLYKiEEKwbeVoco1gB3JsJpPLMfMbGmPruwqPlmNLSpkon3EiAvcTbr24GlyM2IFNNlLJ5UiPwbeSYPPdi52IsIlMJoNHxHwSkMhrJsnWtzweLcyWlMoXGB8bx7eNy7qM3m3eKt6w2CewtQS2+qMSZXGhdH6a/9XQVcBVwe5mOPnIPrHtE9s+se0T2z6xNY7Xz70X3MMe9vC/Bf8JAAD//0b4Hd0ARAAA"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取应用模板中所有版本的version_id')
def step_get_app_versions(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    versions = []
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions?orderBy=sequence&paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Csubmitted%7Crejected%7Cin-review%7Cpassed%7Cactive%7Csuspended&reverse=true'
    r = requests.get(url=url, headers=get_header())
    for item in r.json()['items']:
        versions.append(item['version_id'])
    return versions


@allure.step('删除版本')
def step_delete_version(app_id, versions):
    """
    :param app_id: 应用id
    :param versions: 应用的版本信息
    """
    for version in versions:
        url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version + '/'
        data = {}
        r = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用版本
        assert r.json()['message'] == 'success'


@allure.step('删除应用模板')
def step_delete_app_template(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    data = {}
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/'
    response = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用模板
    return response


@allure.step('添加仓库')
def step_add_app_repository(ws_name, rpo_name, rpo_url):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :param rpo_url: 应用仓库地址
    :return: 应用仓库的repo_id
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos'
    data = {"name": rpo_name,
            "repoType": "Helm",
            "type": "https",
            "visibility": "public",
            "credential": "{}",
            "providers": ["kubernetes"],
            "url": rpo_url,
            "app_default_status": "active"
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询应用仓库列表指定仓库')
def step_get_app_repository(ws_name, rpo_name):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :return: 应用仓库的repo_id
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos?conditions=keyword%3D' + rpo_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除应用仓库')
def step_delete_app_repo(ws_name, repo_id):
    """
    :param ws_name: 企业空间名称
    :param repo_id: 仓库id
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos/' + repo_id + '/'
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在单集群环境创建企业空间')
def step_create_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata": {"name": ws_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"template": {"spec": {"manager": "admin"}}}}
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('删除企业空间')
def step_delete_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('从appstore部署指定应用')
def step_deployment_app(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用版本号
    :param name: 部署时的应用名称
    :param conf: 应用的镜像信息
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": app_version_id,
            "conf": conf +
                    "Name: " + name + "\nDescription: ''\nWorkspace: " + project_name + "\n"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    # 验证部署应用请求成功
    assert r.json()['message'] == 'success'


@allure.step('获取appstore中应用的app_id')
def step_get_app_id():
    # 获取应用商店中应用的数量
    url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    response = requests.get(url, headers=get_header())
    count = response.json()['total_count']
    # 获取应用列表的页数
    pages = ceil(count/12)
    # 访问每一页应用，然后获取app的id和name，并将其组合成一个字典
    item_name = []
    item_app_id = []
    for page in range(1, pages + 1):
        url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D' + str(page) + '&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
        items = r.json()['items']
        for item in items:
            item_name.append(item['name'])
            item_app_id.append(item['app_id'])
    dic = dict(zip(item_name, item_app_id))
    return dic


@allure.step('获取appstore中所有应用的name, version_id')
def step_get_app_version():
    # 获取应用商店中应用的数量
    url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    response = requests.get(url, headers=get_header())
    count = response.json()['total_count']
    # 获取应用列表的页数
    pages = ceil(count/12)
    # 访问每一页应用，然后获取app的id和name，并将其组合成一个字典
    item_name = []
    item_version_id = []
    for page in range(1, pages + 1):
        url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D' + str(page) + '&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
        items = r.json()['items']
        for item in items:
            item_name.append(item['name'])
            item_version_id.append(item['latest_app_version']['version_id'])
    dic = dict(zip(item_name, item_version_id))
    return dic


@allure.step('从应用商店部署应用')
def step_deploy_app_from_app_store(ws_name, project_name, app_id, name, version_id, conf):
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications'
    if 'edgemesh' in name:
        any_node_name = cluster_steps.step_get_nodes().json()['items'][0]['metadata']['name']
        conf = step_correct_edgemesh_conf(conf, any_node_name)
    data = {
        "app_id": app_id,
        "name": name,
        "version_id": version_id,
        "conf": conf
    }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取指定应用分类的category_id')
def step_get_category_id_by_name(category_name):
    """
    :param category_name: 分类名称
    :return: 分类的category_id
    """
    url = env_url + '/kapis/openpitrix.io/v1/categories'
    r = requests.get(url=url, headers=get_header())
    # 获取分类的数量
    count = r.json()['total_count']
    name = []
    id = []
    for i in range(0, count):
        name.append(r.json()['items'][i]['category_id'])
        id.append(r.json()['items'][i]['name'])
    name_id = dict(zip(id, name))
    return name_id[category_name]


@allure.step('获取所有应用分类的category_id')
def step_get_categories_id():
    url = env_url + '/kapis/openpitrix.io/v1/categories'
    r = requests.get(url=url, headers=get_header())
    # 获取分类的数量
    count = r.json()['total_count']
    if count > 0:
        categories_id = []
        for i in range(count):
            categories_id.append(r.json()['items'][i]['category_id'])
    else:
        print('无分类')
    return categories_id


@allure.step('新建应用分类')
def step_create_category(cate_name):
    url = env_url + '/kapis/openpitrix.io/v1/categories'
    data = {"name": cate_name,
            "description": "documentation",
            "locale": "{}"
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.title('向应用分类中添加应用')
def step_app_to_category(app_id, cat_id):
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/'
    data = {"category_id": cat_id}
    response = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('删除分类')
def step_delete_app_category(cate_id):
    url = env_url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    r = requests.delete(url, headers=get_header())
    return r.text.strip()


@allure.step('删除不包含应用的分类')
def step_delete_category(cate_id):
    url = env_url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('修改分类信息')
def step_change_category(cate_id, new_name):
    url = env_url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    data = {"name": new_name,
            "description": "documentation",
            "locale": "{}"
            }
    requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))


@allure.step('获取应用商店管理/应用商店中所有的应用的app_id')
def step_get_apps_id():
    page = 1
    url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + \
          str(page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
    # 获取应用总数量
    r = requests.get(url=url, headers=get_header())
    count = r.json()['total_count']
    # 获取页数
    pages = ceil(count / 10)
    apps = []
    for page in range(1, pages + 1):
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            apps.append(item['app_id'])
    return apps


@allure.step('查看应用的详情信息')
def step_get_app_detail(app_id):
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在appstore部署edgemesh时处理conf')
def step_correct_edgemesh_conf(conf, node_name):
    conf_new = conf.replace('your node name', node_name)
    return conf_new


#########多集群环境############


@allure.step('在多集群环境的host集群部署指定应用')
def step_deployment_app_multi(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用版本号
    :param name: 部署时的应用名称
    :param conf: 应用的镜像信息
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/host/namespaces/' + \
          project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": app_version_id,
            "conf": conf +
                    "Name: " + name + "\nDescription: ''\nWorkspace: " + project_name + "\n"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    # 验证部署应用请求成功
    assert r.json()['message'] == 'success'


@allure.step('在多集群环境的host集群查看指定应用信息')
def step_get_app_status_multi(cluster_name, ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/' + cluster_name + '/namespaces/' + \
          project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群的项目的应用列表中查看应用是否存在')
def step_get_app_count_multi(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + \
          app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['total_count']


@allure.step('在多集群环境的host集群的项目的应用列表获取指定应用的cluster_id')
def step_get_deployed_app_multi(cluster_name, ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用的cluster_id
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/' + cluster_name + '/namespaces/' + \
          project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群删除项目的应用列表指定的应用')
def step_delete_app_multi(cluster_name, ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param cluster_id: 部署后的应用的id
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/' + cluster_name + '/namespaces/' + \
          project_name + '/applications/' + cluster_id
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群从应用商店部署应用')
def step_deploy_app_from_app_store_multi(cluster_name, ws_name, project_name, app_id, name, version_id, conf):
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/' + cluster_name + '/namespaces/' + \
          project_name + '/applications'
    data = {
        "app_id": app_id,
        "name": name,
        "version_id": version_id,
        "conf": conf
    }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response
