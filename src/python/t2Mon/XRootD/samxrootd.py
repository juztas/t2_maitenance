#!/usr/bin/env python
# ########################################################################### #
# 
# SAM xrootd file access probe of CMS
#
# The probe consists of four steps:
#    1) try to establish a network connection to the endpoint
#    2) query the xrootd version of the endpoint
#    3) open, read, and checksum data from a local test file
#    4) try to open a foreign file from the endpoint
#    (a fifth, federation check, step will be added in the future)
# ########################################################################### #



import os
import sys
import errno
import subprocess
import zlib
import random
import argparse
from XRootD import client
from XRootD.client.flags import OpenFlags
# ########################################################################### #
from t2Mon.common.configReader import ConfigReader
from t2Mon.common.Utilities import checkConfigForDB
from t2Mon.common.database.opentsdb import opentsdb
import time

def publish(args, timenow, site, error):
    publishdb =  'xrd.redir.sam'
    if args.ipv4 and ( not args.ipv6 ):
        publishdb = 'xrd.redir.sam4'
    if ( not args.ipv4 ) and args.ipv6:
        publishdb = 'xrd.redir.sam6'
    config = ConfigReader()
    dbInput = checkConfigForDB(config)
    dbBackend = opentsdb(dbInput)
    dbBackend.sendMetric(publishdb,
                         int(error), {'sitename': site, 'timestamp': timenow})
    dbBackend.stopWriter()





CSXE_VERSION = "v0.01.00"
CSXE_XRTD_VERSION_BAD = ["v1.", "v2.", "v3."]
CSXE_XRTD_VERSION_WARN = ["v4.0.", "v4.1.", "v4.2.", "v4.3.", \
              "v4.4.", "v4.5.", "v4.6.", "v4.7."]
CSXE_ASCII73CODE = "0123456789abcdefghijklmnopqrstuvwxyz+-*=" + \
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZ.:,;!?_"
CSXE_FILES = [{'name':"/store/mc/SAM/GenericTTbar/AODSIM/" + \
                      "CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/" + \
                      "A64CCCF2-5C76-E711-B359-0CC47A78A3F8.root",
               'blck':3669,
               'adlr':"3beb28cf",
               'code':"Z4D:NEb+Zb+m9o54w54tQkD3YbK5f6gq4QNQPAH_P9ZB,ND0-T" + \
                      "kdUDXo:Ybw!IYt95D6ST*A;!LY3yQ_?qA.vPK5Tzx776O0Cj9F" + \
                      "U4P7h;hqylM7YNYPQ:zmJ=0Y4TYHkU-Xznf8fGXYYKl2?C4Hzj" + \
                      "aDiFyiLbGCw-IZVYF?ZISIJR9F+8E;JykWh_J2V-e1-GfrJ5p=" + \
                      "CbfJgVfbpEn8Q1smLAWO5QCg.UYkZ0zGrNV:mse0AUaq;P;1Po" + \
                      "Z*!?WyZP7GGwns8T.Iri?KUPjShC6w*bW8hBEeKrPktVB:CrZu" + \
                      "7Hg0eURMFMBW1IAlLlS+I*lArUUe-;_f-_hA.!JJ3!a*0AA=0-" + \
                      "vqqcqkTA4kmliCNsThuH48EyUFgYe!9S3t0H6+6qYwtDS6K?L+" + \
                      "QG?7TZy7r2pKjy1*2pDqGGJsxJL1Em4*c,RDEmAWwV_AA1u8Kc" + \
                      "bRZCad_SR-vqnWPdQ+7TYhr;_KA+_IYXBHr:r.;m_FXl*+,?d-" + \
                      "-naB*=+UXZtCcm7A40a7E:Fl+FU5Pd-Jd*g3WHryVc+8G2pTl=" + \
                      "ygC+qS.,r-ipi?V=d!r*A,nhBmF5Jnd+s7IN26!s6mFcKiVb2C" + \
                      "P7kH!._3?_55;xNlUWG7k8V?ylgundVK5h5S+wwwioFiVrsFrY" + \
                      "M0ggigg0iovX2o+c=ZP9ACF!Y;mkM--SPf2=Ym7ejnhjFvQTd2" + \
                      "hhKc.MqifLRUwpHXY=:Xz,YjSGY5hBN2AW4k!Xeon!Dnt26jE!" + \
                      ".Ekxs;Fxfyc.HXT4GYlNss6KG.ohNAA.yt?z7iQo,L+_P33gMn" + \
                      "d64E!UeJ9mzm:,NH7Lp_=dPKGIRW;jvFXs+6fF5d7!Sml*Ws2f" + \
                      "K=B?cBPHFMtnmBPL0SokSdIYeC=WkULQOfFV.?qW_MmjLg?v.p" + \
                      "?wxqfnQ8:gCXxmXJMnv0bgNUjox9,ckg3eMA_93PRFLJ5K8hT9" + \
                      "XzTxqGk3:tZJyVMS*NzV6ijxtp=.Yh8Up1Mlnm,S_,_;4r;br1" + \
                      "Q2VmYVpO4vj8IcSupIAZ_9P!m-ftmH,Vkph7q3kwbeF0gJ?Q!5" + \
                      "XqxKU!z0Fohq_R0GBJo7Yc1ea0r6jWPT2TcgqVGy_Sa!oDQd7." + \
                      "vPibLt6Vj0jKzrPV-P*t:a5CFRVBTfqS_sv9jFmkLqIp;MAEFO" + \
                      "K4jsM23qIgFM_dyu!2uDK!RH8w;yk8KA_fVXA2n;+fx5GV=Njt" + \
                      "AT_d7kGsl::H8xSL3bK1D6fqvSCvn*G02qPgldQmLgpDy1SNs-" + \
                      "n.UX_QotKlcmYyg.wiFLrhAyMNo4ZzygszS_f*OhD6AsyUkf_D" + \
                      "O3rIWlb_f5:BlkcMgNqO=CW9Nw9tAJuOycC03R:uweml*Ymjv4" + \
                      "DFuN3BiNuaTR-aO.sXmffk5!=buw!_PbiP,xMetUt-HOgzM;.7" + \
                      "p5O0MwP_d_vlpid.23?OhfHD6SZU!nEmXiY6i4C2:x2Vo;tNHi" + \
                      ";k;NQR=c:1pYws6EMEcXx2nt,fHSvN3rek2Zrjt7XhN2NCqxF-" + \
                      "qPAZ0ry:IBYKy9zv1-+6C9,IKey7GZlDId5UT*7DIOx=,npZU+" + \
                      "qz.E?MF!=EOgrjh:R7Br.KmVUnn;:_ACTVi4gKvc8C9NkBZ_Kp" + \
                      "!RaqqE,NC5lgQKwBKmKQ-i:oo7du*CtB0qqXzbZ0b+w6G;pU3l" + \
                      "UTmT1XAlB3gcHJNS5X4tGQMicZ5JwVPKmfOY+TK9z1G11NJc6+" + \
                      "Il4NE?s3PXno2A_=-S;Ygo4jtkDNeQ=r*O6YFgk9Jsz-ovr2m-" + \
                      "KzPH7s1fgCwAN-egvA1oIct5BYjCiPj4SmUG!cS-N?rjttgiHe" + \
                      "B;;OiqizuSV+N4+CZ9NfsPP.RXn_.eI!C,:*02JtqQU;9y++A-" + \
                      "3fDAC;!tAW16usfK!!vgQrtLJd4VZdc.6f?,h-9Ns*JM6XpWOV" + \
                      "=IS,i-DjkDqw5xsPa9ARb?I.2K2gw;W5sop4ji:K6cH8PIU!A:" + \
                      "IzX9xVPia61KMaRUHj!1Anm9wiZBsI-!Zcm-10YtOF*!Pb;y+T" + \
                      "w=AMrJ,-qCaM3IqBdbw:;J*ym_dQwaOtXKU.!zL:DL,698k+a=" + \
                      "YGgf,NuueP2XkLJV+6o-1KIP*DhX;rGEmGK;o4wfu;wHLzAfM!" + \
                      "otjY0+?c8iEvpiH,=LdiIbKLx*+pKGOdp74up_bgK6K8Dun,ZB" + \
                      "F=!u:UC:VRIQt8yy8UMAzPYSme!ZXMTIArWw1u_j!hjO,Hg!a?" + \
                      "J,LZIA5Jcn+V+*-=povi0ohnT;qdrTjIct-JYxUb1nNW5Q*2sX" + \
                      "womr:xEQrr,PIeGLfkP9Cjifx=j!:?7=Kl1w0BGJE10QmT!W,M" + \
                      "Toj;DrHQcvlqHHC5,Npwp_:qdDPG0WSTqs9VboD_JloANI;x1z" + \
                      "xg-VeWpe7mFyzst9L.Ki-9+5nod+YRUx7:MfdK6ra0AYxOQTsh" + \
                      "TZsjoYFd!c6iW7=mVbA4180WuoaWKvsu-3Vua2fADi:pe9vlw=" + \
                      ".Rdp_l!29yOmmoY?oj0?jvKvEyOjrJ2_Kk*;b0ZIy3K+0_C:nv" + \
                      "jZutbnUmcoP_1tRS7*!EKC4U?H0tz8Dfa6Yx7e_3RXt:mEg_Ij" + \
                      "4OC*eY;RnyyKxv6:8.5g7BGEzySy58Mz7a6m8;?m6IkYQ+sWO_" + \
                      "T.oLYe6X0p2QVj=QKO8V-Rbq2vUl4Gh;fD0zAcFvMaBLYMMNbh" + \
                      "txuSeuScso=oPm87FTlwUr?q:B-!OICPZZ;Q!WLL_Yy*cORHJo" + \
                      "TD?7k6OuJ:;xIYvlDHBxnwaL=P8MwWeR2o?LoRi0!-?tB;nUHF" + \
                      "+nP:F++;kM=OmUST*_FHJYpCRI6Auak+*jdbD+DXL_OewqaxZe" + \
                      "cYX_NikuXd20VwPjR+F;Bs4H:7+.!oYI1mvj*94Tvi0=wP=erY" + \
                      "nfELvGf4q!XkyLMt-.rBXqbvX9,XTW,Z,EhNUhtoV+=r2KaJnK" + \
                      "8EKR-K5k,ViJrfmMU7llB*K4JEqadWm=wvQfKEEYIj5kU.y7ya" + \
                      "ah1!=bZ*L7nw*F7_cGMXL5lHgd:_kPhvaqRAUm3eP_0cEBjbzH" + \
                      "IAh4,BXULXZZd3AcYVKzq.XEIDSt?zP8,0!KBJ9qYW7WNXDh=J" + \
                      "kPPA:wGu2qkbBH1ONh7?B_0dg84guZCO9.aTwIBrrFIO!s9PdN" + \
                      "-GHYa!+rN3fh_DbI2Gaoak2_VMZiKhy4gWD;I79:Kh=EPYQ,N!" + \
                      "tMV!hYPzqcH*rGoTI2!P7Mrs39ofX;yL1tcwL-:CZg!zO9h-d=" + \
                      ",Cj3A-dY:OBBnY6FY:2pYRngMoOgRNzp*fmAZTG8W.P3:=0qZs" + \
                      "2;CyEIsnynUE*DFu-rPbh4fE4S50QsS8WG35Y;noQSCd9t1.I7" + \
                      "_fu.S-vQphynsva+mU4ww,TXz5GTKMhv9mrxQBRa2t?sGp_0-;" + \
                      "n0.QUSql1=O-dK0brSes*uuTu;n7s4fkLQPNR_Lr5Jj-CrmYH0" + \
                      "fiH4AhLC*Dabn9RuZTeONqBD2kCm?b7=oqf8hOKq2mWD8,_.79" + \
                      "w8xu:KiQ47JZFSmeMWzN1Wj_1TBQ0zi!nHSY6ICfC_nSb,.59e" + \
                      "NieqpHDagb9.!4He_cqH5,YL,sMstSWPyPBXNsX.wd+1+!bnov" + \
                      "FwAV,zz5!zuoRSHtfAfhdCX0e9hCR0mOyQ.T94HSBLxsArSWF_" + \
                      "DMOVml6N3.0o3MFe-f*PBUaB;OqN!KXb3?9UiPthZ_-Mk4d*!2" + \
                      "bjGndMk3T0Pcbe=9j4n"},
              {'name':"/store/mc/SAM/GenericTTbar/AODSIM/" + \
                      "CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/" + \
                      "AE237916-5D76-E711-A48C-FA163EEEBFED.root",
               'blck':11547,
               'adlr':"77fa4064",
               'code':"+JaLR+8FsW5V:533fW9LPInlv2jRB4so9kI?,:+dWhas14.Sin" + \
                      "0mXXcp3Hr-t7rH_9D9K_ZgPKxncG-_g,4nuLFB-+Swp:TU9,A;" + \
                      "kxTT1-IhlrGD9mFyS!*ad3a?2IBOgojQngVfaZ_aZ_e=M:TC4u" + \
                      "IgTPKvSf7b8PdpA:xT6JIRFTu,mAY2mOHVy_k:=Go3n:Wng5=g" + \
                      "tjyaCUrG!B?9gm.TDvy2PWEmPx_bg615pCkLUGkT2DPZtGsb!t" + \
                      "-CiPN:?wT3hu8tzR2_;!pv:qQTJj,YhnoiGs6ECet6=o;*mGZg" + \
                      "u6IfL3=OK5u_Up8*MJEh!i,WzmNidyGdYL2zMEF3Ecw7XpWfqw" + \
                      "UAO;U4*h;4v3SCi6L7:vbZiCN03tfjNSDrrb6kfQNU4R6dVejT" + \
                      "UDcvmAzwmeNmvKC*bhT;brQ6c,m+=LI.1t_LzqOr-ygyg?csos" + \
                      ";*4l214HeU8x?Fg7:Q7K8i;cHpQ9fAQ,yfRBfMh1DlqUQvhFS*" + \
                      "cjZ3PBAKTg3r6J9rhU,9XaWSn2,dTpkp-GAQZ9ixcU_sg9bID0" + \
                      "ZdC+RN*x9fy._WAuIThEN!HSNkWOdd9Bu5Sn!QhrjlAabw4G17" + \
                      "8wgBBkI=!qcVbE,*mlil:0=Ak*Pl2H3Ts:_.JgirI.*fbMVZ71" + \
                      "E6_SYZ;Kv977i8euM0baQ9Fn+jnhQr=0WWQGeML.U;7b5cj7Z4" + \
                      ":.N,o=abI4;vvr*+sjMxtb77MI,h6kUUjnGRNc;+tBax,3XPq6" + \
                      "_?c=Hgj7ee-aYaKBToIZFVQ?DxqQwBht3,eAdXLjmRXqbcbZ-?" + \
                      "Czw84TKMLtj.y8rD,u_YknpEXNDRlXeoU1.i;L.*_wN0eg15KB" + \
                      "yo+U9zVRxGb4i!Xgom6*CMyt;dIlsqMh7Ly6weSWQqnT_;Iu:v" + \
                      "f6?Gvb1KD!WWS1-rr+-Rfp_3OB0AHXG8SJ9obA;?Y1:?1ElgQ5" + \
                      "shgrPNdwuwbm7e.y3-.-gpvZ5n6D:.Gq;jH-zxzg.hqjgA:zLa" + \
                      "YApIrqPpM88,RWQ+FVoipEJP+rsE6E7d1*dHA0B_*fN1ESB=W5" + \
                      "NWk3dZK8fB6T4fZf+yKB:7aSIA0oeL=An.qXaxS8Gb+kM*9z;N" + \
                      "V+g+XW0xI,*b12wJO7qGbMsn0g9vimTH8u2*brzA!Q9pzAILI-" + \
                      "Ge*-IMYCgufrQwKGt=CXu3NF7;DpR9?jYNol?vLx0P4=LlM078" + \
                      "cx_cuttn,FXCx8_PXHO7ilOQhanRcPXLOISOoWQjl9;cs1Dj5w" + \
                      "9=O,,v6aEGJBN7_uA3RJ:c!uiFjOfJMop8aWbjNvhUng0bxWJ+" + \
                      "0.x36d9F81F,yq1!qk7pC--d+O+LcfeCt3AoQX4H+Hw=_*Bac_" + \
                      "WX9,B1aRyc3QWu?dEn8M0BhB*xhlD*Duc5oBYEDF3u2EXs-3Y4" + \
                      "S4vzsSMSTj:7w,Gz59r5?vVMQJ.U:vGZPew2NwBIrAWq+7AHma" + \
                      "YG7.p;9?MKKBUDrEuzn8qV?toebQf2WQzU=4*n;h16ZRDVQ02p" + \
                      "HFzI9soU8u-DUqKH4Wg9w7nh?_U2rkAOKm4:Y8QuvKfNG5Tt+v" + \
                      "o-JmKjZX*!=iX66xFEI7Yh!m=VGHdthQSRzbL+LE4tNwNgAJas" + \
                      ":jBgWgK5=nA,?XE19rPoMN6xk1cLWDLcn-sNqMK*7,QWE5tO9G" + \
                      "jgqidJSgVh.vZoh=yOy3l5WaQw8zSGvMIqOw1=4PbFNa5ZQdK;" + \
                      "C29,5L5=BgPkNccH79l+AxJN449AaaPi:nH;=CyI5?NE3JhnDy" + \
                      "S*OXJQQiUxpyme,?crW*Nl!d:_:,NqxsAIgu5crYHuo5?6NPY." + \
                      "zfgQ-,-eP39Tkpaj_!GxNydPKhi;cfU7muk;5jYb=+l*.13DU;" + \
                      "NcpjJctRlbAlk6NL0z?SLz5UPeR?CLzKM=+A3B__7my4uHLVVx" + \
                      "p!u?qc.b-v=si6LiodQrzM!hUauL6*WgNR1d0GVrNKG4pvT_rs" + \
                      "rh_Cgt1o6Jj:4fbz8QG7VFa.gPVRJq6ZEXATMHZ+CVu?LbBavR" + \
                      "xr=HHMafED5.5VzxeVU5,b?ScQpAlxAklCqxMtDofe,TqF+PQ4" + \
                      "IZ+.nd=6;;2FYjwQ_ZD23Qh4,=jQ*Xaxo1Lf0*:kUS.mlXRQH8" + \
                      "*E.?mC6iTt6C5;J5j=WgP0FmgdUA_N.PS5kSl!eYYIpTDlgx4C" + \
                      "CousidU+qdMj0S133SD8AXgndhkAkoYzXvUmDGJX4Zx2rWXT51" + \
                      ",39bNXf5=yL7!f6W3d,allGSjeqi8BY3?Is24=*sdmDK02xU-;" + \
                      "bM7zi5i=YNgu1=NM!sbbyc-nPMaxmVNVjt?!_ClK8?qErs4KDE" + \
                      "y+-Pe3Ja=Urz?1?,cRPrkn.Y!+QuzHQy0zPjVuZcyKx!XMxgZO" + \
                      "1fggMN?E40xg8V1C6E!Kof1pf=1SWcKGY=*?-boyuQDCqUQCkf" + \
                      "9HF=Gx0fNpuNR7oQz?CTHdeU5h:B;SPJ.C5=NS13yp:AWmmq?r" + \
                      "2LZNI0UALRn0b?weB6qUfj;TTOohx_r:FHdco*2FZ8W;w!fVGb" + \
                      "GYYH6pW6jHDsq6oBcHxvgjWzpm.nBNZ=slfs7;n-s9-fFk;Chf" + \
                      "SRD7w:iwS,zkuwe-TO2k+rKROZoFLUPwi9asIvg_++pDUuiR.h" + \
                      "x_F7X7ieX6_W!Q7l,DYp*_iw6Wrbxn:l=ntAReFDui9l?17+yB" + \
                      "?VJ0NeEg1tEaaDqNw;5S=;HWyAz+t2eZRUz;j!9!SsnGFN*9.-" + \
                      "NpSG*fQgWp8FJotMurXBKz17,nSWYIzvuwcgtjslBn?!HgnHI2" + \
                      "pTxwQkQkt13,D9?5Ht+BjVC7hoXB_pE!?6VrCbe*oEZ3WxemY3" + \
                      "15jNSm3_!;PM0a;2j9PqeshAADQsgExJm7uST3DjfX;xji7E+R" + \
                      "8nEIcCF8b-YgNKBvSUhDls9nj,Z-T;8!V-4*dex!WPGKMZfO5J" + \
                      "nZEh6-r+PR*4sVF6hhl;8_V+J;iGL1-VejuBWZXK;+shim?r6v" + \
                      "6De=:7bRTTYeGw=HKiWweO9Gfz1pfHy525f:siHwxO-52*=IRa" + \
                      "t1,4cxZS7UGLBjb.3xtwqNmE5UzTpLmqJ.IXkHt,_!mdxS_um3" + \
                      "_DZ4oT67*peLmv?25R?wiRYJ*z5bru=0cnREoX9raar9H!SrLy" + \
                      "cM-nJT,m-TL3Z1Q_W.j,IAV*G3jRU-ON-VABwJtPYpJ:;KKXTH" + \
                      "nueB8Ri-A-vAv.Gb3B+Tszr,Z1NH+xd4R3Vb2!CK=VLeLh5is+" + \
                      "fnI!?3;OGsfv62VBYnJYR*DGJT9UbMs?q0*6h6UFy!TMPr;sbC" + \
                      "_U;*fJ_G043gRh1oz_6bU6SRYkz-U_UphMpBlfoA-!?f:Lj9yr" + \
                      "bX=!j*BT33l5edjKWs,BvQR+,IEyk=!zfJmkPA4BqBSSUHKG*4" + \
                      "+fDV0UaiXK8o.qLt3VEaKZQvKkalXu9jgZVQ!*CAK-2pd.J8jR" + \
                      "zNSKu+pALk!j=;n69x?q;10-dl?pFJMWoKTZUMh?fTogPpVwgE" + \
                      ":n,jdMd!xe:BEeJj0JMlGW=S.bdK-OMfbad1W0A*7g;?*!et=a" + \
                      "wCPKkt=NQsDf;owM5CsdIAOLe?k,t.exfp8QaLzlY7e.B0+v;H" + \
                      "A?7eyT1eO3cy:XXTzH=B2yKSMGWlDW8.GVcX9UNOu=PASq2exZ" + \
                      "dnfZ;wlzFk=T6aGN;P-xpH!?pM6NbTDuoZjTm0PmykL0aNcUwj" + \
                      "=5T4gI9-lyLI:kDFv8sZNKlsC.6n+u.d4X_2rnPmkh2=kO,KcU" + \
                      "vG3M=+**aVsPcREIo6h5+5n9L7U2NlrjzwfuxOO--;0c53QbvO" + \
                      "kr4::,LmBfIdF-XvicoDRYaEOunQd!P+wp5prtcdnClveKZ!_1" + \
                      "bE0rH2eR1fWAJJYgv8:c=pS374892*?lH.jvz.dRwz0k-sv.fT" + \
                      "P;8:xHF,hF7VVsWIri0j.8r9UsOuPnbA_,i2synLF=gbsRM7dO" + \
                      "EuNaj83GH3sfmXg_1_6BOf+TNfwVMlnM-?pvQroFEW?D_KS?ng" + \
                      "zXOF?3RJeKyxE!M5sOFhd*oNCOxjrtP?ZN4Dq-VkxAA+2,:3hk" + \
                      "qOj5rNW7u1x?!Om7B_vOc+!H9W.nw2KAdpwliMOu04vwp0+_BR" + \
                      "o*WbMgRCpQA;:8Y:?=90fKz7II9RKmU5HD_WhnKn;cD67vN;=4" + \
                      "DaH8t!U3:FGO.OU:?:rZorPTu-zrU;2H3B:xS.51THNX9eAz=n" + \
                      "c=cBu+6otJ3ILaPT3?Z3LulKK651u!2IKpFM3JNFwAeNGJ2ybJ" + \
                      "rAZGm=Qw0dKqbH*VU+!Gpm*sTL;A;k4Wt9Wx_oPcG71sz9Bx*W" + \
                      "4.KR+=WBYJy+i6cIU85K=x;NXM3sQHbE;7Nc.*1:FNsXmuG61p" + \
                      "MQjA:S*bi*AZySe3Td3i9wNDk8d+Zw4Fc3e?NgRz25c4suYc8T" + \
                      "xA=+C,bAhogugWBeTHJh-k?TyU32pfjvU-x6JadW*4zln_Fefv" + \
                      "kM,XmfPmH?Ol5QYvcV3xHfgMKNjVsazbB!qBysBt-IzX_g,0jS" + \
                      "CVBO4n9mb85dTpfU3c4C87DfM?KlZuM-t7;M8pa!g-ziozUP:Z" + \
                      ",K-AVw-BeWS_?r14VeJ8-oSmx*P0:SCv:nuI_EesN6Gdg!rDo8" + \
                      "cCyvjb!n+=.pjaCCh2st05:bS:+*ZKJ3fH*OOeFZPtfRocminR" + \
                      "B5o7qaf73KwIJBplV0Lo*pI9,;t*Hvt?C1.A7kj+BQs7NJhf?p" + \
                      "ANJOZeJW49QLI4z:R1v=*;E874f!236UK-OWhlg-T.DSVetAJU" + \
                      "2Fpryca=CV8gT*j1Y9nSbdbXc-zTKq9FiHQN1mq=2IaAIrldPc" + \
                      "01WueKjYE,MwEMbYh.sOd2QDDcGQ6x0Jcow+vsIoxQn?tmU7QY" + \
                      "jWk.z;BU7tkQl,roydJFY:ZAD8j3Fcr5;:sOJdXOMeSYos;i?A" + \
                      "xrrpkaxyri,cGGBjaW.1qN1pQqRHjmce!yIH:N!Lg-JATonWxo" + \
                      "HF6zwKh5++2!fv=cA6N6z*vn!nEKBG.ADaCAIc+Q_y0zzQnY;;" + \
                      "qfFbDl0ecqwbl=4lz8VwWz!IaIQRqgVtxWRmBglz2JkIzwYknt" + \
                      "uzM-pd5OonAjblZ=ucKnhbxQwkqdBhXE8R*cN;M3!6p9raHcIL" + \
                      "pJMbTOovwv.qVvd3_c;Xj1x.tV185lc3FH+yogmTpX3FK_1Ju*" + \
                      "UXNzpgVgI,JZK4PVTRTN7ijkspEoU;0?5ncp,K9EdZz;a2Qq3S" + \
                      "=U3?+iKOgo4pVLxNFq!wqT1hCg5KyDSM+!XWKD:+oaj2CLjVWL" + \
                      "OFaJ+IsUn58_GGZzNaan+MMF7KrOEa;KjG5IDodC;?t4KvtQ9b" + \
                      "p2gEUKXolOCxP7qrXl?HdVYSb.Sf2qcPMzTi;N46IY0.hBzLJR" + \
                      "i*.91Bt+;.P?TGO:YFApniiE.xNx9ColRnM0vst;p+,F1pWUfa" + \
                      "=Slwr.BTC6z8LIeXB3FS_.BiDLhi4+9qcHsgH1uOFx8U-N6Tq;" + \
                      "!cR.tjL!qcjukDDpDU0uP=tvvlkJkP=TaYK_DiR9S2k0LdL*I5" + \
                      "xez4ZCbJfB07LQ7Eqm1roXtzH*=i_:BaEX0tWt6D!6_;8aYddZ" + \
                      "jN+XKvAMDsH1xLV;31DU3R:Sd6_NWp-EBpttkAO+kKuezh6;Eb" + \
                      "KQTrp2BS39y0wPM6O-k,PSuFnIspiJeZLYh2B1ScN,3fK4b.Fw" + \
                      "y4lzRkZAoc7OeH2bW.lRj+7-pgYa=*W2o4CCQxtljZx5y8SqVq" + \
                      "S*jAQ;Nh+rmjmI5d=pxqxQ?+zsOReYSHZDoJ!ISuKV*:cwmcgs" + \
                      "CIKdyWWX1be_lw9slxYfTErNASOzqSt1S2k?G8ZL*kndvrmAbi" + \
                      "c1E1V3MgCk:qrmkeE5Mh7ywk==aFP5,TRYP.FN!NM5da5az=5," + \
                      "XU0Rb0AF4H!rP6a?vUZ:Ob!CodI-KtNq9Vry::p;675j5oTZ!M" + \
                      "DSAFd6KK?d+IDY6MTOosDZN?1,WY6nkV*h2Mj2,8WGnqriseu+" + \
                      "8tV9qSxGiShVRFL+ftmmm:vu=zuSef0!1F!!djLBsHcx5Ax+tu" + \
                      "NGE-c.BKaHkHUJs_omS7GOdps!S2Lg+qgyyf=Fav6M*dUOwwkB" + \
                      "PLC0?e:MTtogne;P0.cK7Z*EGM*;kI,X:YusqGiH?oOZJiBBxL" + \
                      ".ENV!!Y;Ztr?0bPP=OHk*40aByHIfsQ-trhlwy-gAobUexG!Ll" + \
                      ".XN7yc2OWnqP!w:M*lOdEwiiVqN*N?NpdqSy3ghYGRyPoc,OMv" + \
                      "r_=L7ZsAH!fHkF!yyCg6ul:+0nor4tVv4G2K_?+YnZ6U.G6E;W" + \
                      "-i+D_=O,aKI,g10a26iIU4F3-slHy1T.T-;W33ZmqdVg3Gab;g" + \
                      "ED.jiJ2fMIYYqK0eGG5hLX4qZz*t3W9P.lfw1JHN-2K5i;+?Kc" + \
                      ",uiycbx+pAYwtVR_u*CBFTDU_0P_NebF=m0jImivUuQSlww8_h" + \
                      "58_*LmpFG4Y;PS+ktYlRTHsJK3bes+Akq7Fnz2K:jgBBFq+D9Y" + \
                      "TzewimQPx*s-iOVT?!_Oi;bqVwQmstJS8a9*4R,zQT0mh2wDnR" + \
                      "I4g0awN4F7HjFk6O8qJVTN69rgl7xEgWCr-7TQb?c;?Ef*dzP2" + \
                      "dUDK8d=ysPZ?;AOBJKJA=8XdzvrGNNAVZLdDKwpHC7TlSqXeWP" + \
                      "bw1t46FnQ-ockM6*f9rjAmJfzurwUAr9qNRFRGXp.nVvL!st4F" + \
                      "ChbP9g3b8+r!UOzFUR*:fxjlbmu:B,dPY0nAAR4rB6R2!ngrrU" + \
                      "rtRBmFY2v.oVP,?90hvy6?q,jx_?3p;dN2RKJlRkLv2Pq,6;h:" + \
                      ",xHhhtf0EVp9MMKwAC5QehWRkOz6o*59yExHNr:qUHBVIy,,L9" + \
                      "._?iCl5ItjFnLG;F5w_P:POKA57xsWts!xzEMdXasi-ZloGYSX" + \
                      ";GSyB1G3AqsbhoBNitabCudyE_7S,wtte;Va2qfiSvCv!;K8iv" + \
                      "nxOL-65WT0-+499M0tGcEB0W7-SI!1k.2:kY?PZhxv6ZOTrRgw" + \
                      "Yv4;PinxQH..IdC+gNe-!v8d+jLU-XpqLh4K4x2lTypmkJC7qM" + \
                      "7!FzvD5qWMpE_u6h8Zx35iy6RYO6I,VR,O!frYE=npn.SuY.I3" + \
                      "Vz=P-Q*kC-*L-46=wtZXPtwhpjShO0Y.OR:IfA?-*?2tI1eZLG" + \
                      "ktCLgqbwlwhv0G!3D2wtvFz4PpVdxQy_l.;u5:D6=rP6flUEUG" + \
                      "xWQ4+uueIbEYVn?i2qGB;2G.2ZQS9=O=ZpsBe?ZAeg4W8naZ+c" + \
                      "?.Qgvq*vQDkp:L5pnBax4hVGREu.p69oJQOfsnJ:d*bMkrG9DI" + \
                      "QqOACdiU_ZQ4v0WlvYC;2SPoo,VZ_lgu9N-6?Q3bFv?+zL9g_V" + \
                      "mtrG.oMyxlaNqwmp1jG.?cV*Nlk*bH_vbU98w6AOk5ZJuJwLEQ" + \
                      "VMj;sOyku*tKoTx4aGH7Waq;-FAyVvC*wHp9bDsZGizYCb7HLG" + \
                      "AsP09=.bn1rY.WWYMGCGrG2Uu:X3=iPj9+sOgI?WYqkAgrvV!;" + \
                      "Xd;YBRyw4ZarC;_5HunXuS1cW615dX38qde9cdSSF6esBkVpiX" + \
                      "E,ta6,WIB+bAms4g:?:TSI*0-;J2_IZk6YBrPleDIJ2sVNSDCP" + \
                      "t=L4Tgaw,HFlT8tTXt.OJ:EqIxYuZmcJ0D!hb7WJzn,BKC=Wnd" + \
                      "21ZOh-52FdJ*0sVERSipl9eHNdufycsl.Kd.naMP+69jSL4oGb" + \
                      "?37P3V8rQiuaJ::bZf;ExvfyX+,qEIz*M7q0hOVUdTHXaI!It*" + \
                      "ZZHsCbxK4L0JhwsU5xl2pnTGhBvR0W7yZd0R!*jdl.oU=aVEtg" + \
                      ":4AYaW:xNM3ZmIpgooBA:P8GGgPG;zWDvuwJ0JI3?:?NM6N!fe" + \
                      "q1Nqa5;gdS5HeHmUJw?t_-.Mdre2fAfTK:OmIYDx0G-p:JSyB3" + \
                      "L3V0:Q?iW1=5TNWhJD;YYL;hyPOMj8E2:ERk0kH-7j1:OAo-GS" + \
                      "zyID,BQWiUi3mF_.Vt5cg6Sw6NN_M8YEh5+9gyONGCWZ0fQDpE" + \
                      "ME:?fb0011!yJk-okn4O06M_Aj-l1YGUc_;0iIDut*7Y4d7+PJ" + \
                      "Rv*r-SzSzRuaAURcYc3Ou4qAhQ;6k3FIRyW0NYh-DUrQIz2jOX" + \
                      "fo!FQ=INfnEnKhC6KlNFRWY+D1tT;yMUjbhXSDH_Rbfc5KOx5b" + \
                      "+m2k2G*ZF*Sxv1g!!_2zhcf79w7ZCPMrE1-5T3_M_NC-I+DhBj" + \
                      "6XD=2r4jwvDd=nU8zerKavlZLM3B9Q+3Dso8fC7_e?4nxwM+zD" + \
                      ":g9EaLQQ,SZ.BmbuOwfF7dgxMn9Ip=aAt_FnS0UJlu;_cCjw,A" + \
                      "aJ?D1=FzRkNWl!dddx.I;mAwk2QfLlTZLyN;AF*52ZFZyRJkak" + \
                      "4tw,!bXUtd1TJ=GWdji25BuNCD!k+!,gZUjLNKJWMfNpmaH64S" + \
                      "-c+-aXzRY2w.nsFRfbk=AKtNA17u7MJkaVkxx75Qms*tT6a::C" + \
                      "vScnp5xZ!8oZboMrh-j1KE,_*2=rp:Uo+CF=UmQxsuXMLDu9,+" + \
                      "eD;f?O?LV8s9yFNB:pIL=2O,ugYZ.3?mVq8J9jREVIN_2y=okw" + \
                      "EWOEqAxIVt0Ct3:9Q:RHCVrFP3f5z+Pl8G9_BbZ-;J8t75rW++" + \
                      "SFtXqYygV1*_fv6Wt4=!i4n0AaJUR-Wy3Za,yKKTKEAy+,OLv0" + \
                      "aKpm.6=vlV9mIDCIZ430u?LDXNpg_enbbkAoUH!,0U5**mUb2K" + \
                      "6iHFbMtnjx-nEk.?dHtAinXdzLaf:ru?uU!ITQIG0fUaKbBLTW" + \
                      "!8zfNVSzp5K+uo!APHf:,bZtfAFuvzAfx3KPE+NKtUV.jsEkVx" + \
                      ".YI2XlnHpXeW!I,JQM5wzT=RLk1*qLgD?x?zMFhqp!N2ZE4JSU" + \
                      "mBWv3M6!cUQtW4GjGIAR-ik_s,EC,;YSo8Xbjn.ST4lHYB1qW7" + \
                      "8;zur0Kl_oEGe?LikT.:Wl?OJTtHYag*c2kcwCWk-E-C=bZ-w2" + \
                      ";ji_5BmUtQiX-?*dEzUJrpmSmqlAEz6?=xGSkiNqP40PAesl+G" + \
                      "JTup;,eBvfxY;Oprx5y0ZRB*:.V4hWOl3xNJnpx-BaCtQZa6=n" + \
                      "4NRIX0F8+-a8cb,Q;,JOnIYVh:IAQDUl+X+z,R80P3V:ti,B:B" + \
                      "f-NK,hX*y2:aNGQ39uAKmllsa0=VDOtP+1UM.8Kk;A5=1nFlW3" + \
                      "zPDIyfE.L!Fpo4qAGHjE,1MXwjF:58GyE8=6Yr+CxOjuSK_l7r" + \
                      "fEGnoSVW5Fet:AG-DHDZZf;NTMHV4LR=2oAboszfzB1SoTR1*5" + \
                      "dc0fA5qcoYs=i:W3JM+6z:K+gDC*.Qj28.cUcB8n_s3*4DfQNL" + \
                      "uK6-voQHR+NPiUGo!B7*UhSTh!7dJJwmCKHN:X4XnYQnW0McK2" + \
                      "auCTlHE07ej8RMbftHvTVaY6l104B.wvF6bDiYvoX_K;b-S4KH" + \
                      "gS;rG2qfNaqF57c1t1Ru3yDe*_E;cWE.DgQcx27gALLQ?n.*FU" + \
                      "DCB.*EhW6K.oQZJAh2sHqpv.*b*BdTSpkJt4I81;R,SwKKWBAK" + \
                      "cXiL67*RvaYxIlFZ5_Q+eYsK59uf=AArjgtyBySaB8V2.rJTmm" + \
                      "ZI9=p-dFR;InJv;OK*UE=yyO_9;ns*ps!dJtcT2?Jy;tR1,*sZ" + \
                      "jQk83cuOh9f0XYd:uvX9rTHJ8_JJ;RKrWfGClNblen3cNwRMJT" + \
                      "3O5WS?JG27ca:ev3!;kZaF!U7,wFs:iK=B=jDJCk,cy!s4cYKn" + \
                      "T5o!hvS;Sscsx7TowZJj9eRw:ttPUGHND=?jVKN.7vFC=LwwjC" + \
                      "xfOG9x5nzR:=;.5jEqjXjhVdcD,.GY--qf,WT2+zjYVTB9!ktg" + \
                      "zgZj.0aC7jU4eaOh:Zy*Dh*O.V_028-rR?kQs-5f7e::0V74ND" + \
                      "b,GFPj_Nh,o?UffI.zyuH7zC,RQApxAUkaKN:hN!mMQHH,=0qB" + \
                      "N+oB;;hUl1QlcAfH?8UmL4TIP!eFuop-5J:IZ0-8g!raUK2GX+" + \
                      "?dlw8LRoqv;8vAgUpTZbVEYGolcUKBCByxutv7-*X8fc_=B8dC" + \
                      "T-rVIji2zYJnjBiwNBP+Ru5HA_SKpO9LLP+5DyYFKuEDMSLzNF" + \
                      "K+0MBw6G;lE5A6;TWZUNX-ZN=l7d_tYNXSg*FAy*cMegyoWxOr" + \
                      ";TBOTCbTQ_W?MiTppN15_Ruq!OKwByL50o=01ar4z+l7_GJuqJ" + \
                      "z7:Jog9dzCv7ycKgN=vTk!lYiIK2F-p-hWOL_9-ORie90Jeh+Y" + \
                      "DAYaVA_JZ8HmzGVmtuF5KXQjv8PCxKrlFi;6dsZ1gq9,xAl5lU" + \
                      "XOdtAhf0qLB4IJJmiTmzDK8bu*gVw.JQL,ae_vo2Fp3klN3,Vc" + \
                      "GcIo-nKprsvcmBVjGbgkH--AwUeUaJJ1HKnHs?Y*bv6A;:oXpk" + \
                      "uLnw*QetA?7B5?5hd*AFKgs0-ej,jsg!PYT3jXVFTFM7H:kDWu" + \
                      "lkF:RGX7IFJ?90kpc?QgHGTaIQoPGo,pMcJKzkszLtf2,FaqOy" + \
                      "*Ig,Ali14VE0nzjxl4O!=Mu!R2=AWT7boQ2n538lPT.7XTh2F+" + \
                      "bJG;foHlZqS-Q-FyGozAQojVdOlwwu-4_2v8H4xLbKH=C.Qj3I" + \
                      "iGE39rK;gOcBJO2Vt*xXitaih?wt+Tm!,vdfDWbR_0:;xI6w1p" + \
                      "L1N-dqB4iE.eoboRatR!dGc11cjLbZ_kmR_RhtjnGii*+?IM8p" + \
                      "Inu_p9xnnsZ+cVs8+hWvGiIvpb3gH6wA1NU:-3bhXgZVctv51H" + \
                      "BY-Vn*RYdvD9mVr;a=wH2A?0d1zsr74J4AFO+B;,oeqx,zdCbo" + \
                      "_zj,1iCRF3C?vU3+kckUxU-s=+cG,IgY6SYL1VsQ,MYN9mhP+a" + \
                      "Cv2Aa,Iz84sb!yhdUgOsF9-iqMg_2,T+2w64OI64r*I+L+e=+T" + \
                      "YR.fu.6-dGk:!jQPJD4e0Aq-mwY+fb2gWfy_wvg!.yQYHZxDou" + \
                      "u!blZI2dE;j?82mrkbCLwx_.gPqH8WfmfDgnc7Ix5*y.J4t_,4" + \
                      "!ni0sQbkYj1H0Jm9vUzqTWfjiKcDM4*h*VMwK9x_5hl+4tb6IF" + \
                      "I4pxXJ.3Mc=RuRPh;Xsl7MT+DB*Pm,HjyFcyi4FmS+D15.jpTi" + \
                      "=8cwnxHEQbJCD2DCUf*P:dcgn0Q!q?S7VX!NxiRLrbRGoPt?9U" + \
                      "L4=NH0ZjOtmiX2QqSCFNy?_1hyL3rT.RO;OexuMu7.J04m.3he" + \
                      "9QNw:;J0Sfu_brhHxQltRyyva;Kyg.g*=vc*kwWhP9IhHu;0gP" + \
                      "PEE0p9+YJv7Iu_M0uwor5?zHy=M+zNk;3Oc1P=-SYYDiE.vRGW" + \
                      "*;gGsziIN.LqGNd44;wjoQzfQvc3,h*4o-WB?3TkJp,iSIvDFn" + \
                      "I9eW=*04Y8kWBihQ1SD8_m6l?.5mMBQ3XwwLlzD_iR8nGtQNeY" + \
                      ":C7VEd+=KuSNM86t=vH3thOWhCybK;MrLxovD-g=ibkVh,P+,7" + \
                      "4zfbXm5mRAZZiqjNZ2P:oSD+ad?c?iX?!QrJpe3__1pX9.A5.4" + \
                      "?fw!iy.tHT_yH7;tEr1kD3uC;-q_jCx,T7,EE,F0qqtK_C:4K+" + \
                      "::.4mtuRLdldNBv6;pEQK?RsgHVGfplMRtrDloSLdWPJ2O;Eqa" + \
                      "9bkXZ_NkgDvLd?bjK4vTUTGA1GZX,AfnIPG*+f;Hxh4Vu4kGxe" + \
                      "2vC9og+j+NTQ6eRqts.qDE!Njvk87X0kukLlAFo+SP=cgXu"},
              {'name':"/store/mc/SAM/GenericTTbar/AODSIM/" + \
                      "CMSSW_9_2_6_91X_mcRun1_realistic_v2-v1/00000/" + \
                      "CE860B10-5D76-E711-BCA8-FA163EAA761A.root",
               'blck':19730,
               'adlr':"b7994050",
               'code':"iHIjSVX,ff9Ssmw8pPM6!9k-qb8ICNwv_,0fVn*_;JOXz8GWGd" + \
                      "nkx4qikRVamlB_3QlG3d!Z;LfVMrjLzL=:+0AV6VBJ0+ZWi;q4" + \
                      "Kd=wDX=jbGb,rffC3OLbvsjfT-WhF!W8UhIzRJ*Bh!!Wwj_-cM" + \
                      "Vn,xB01.YHOYg38sm_YT+SdvEQveS?64cc8V_ZWFbf4ejSRo:!" + \
                      "X9JIssCIleE;BAg2DmCwCBvD:.NkopWHKqk-8n8gJy3Cymtx2U" + \
                      "8Fg*fe;8*ohMrIKeiiDtLvJ6rBd3Cy?W4A?R!-FQYJ9q-eF;,g" + \
                      "MJ=g.xOF9g1PBttV:WgUFt*;4jyLtD7,z;H8sGcdbI4xt+lKN_" + \
                      "eWBi.n_7x9aFis-TiI9UUJ67jKkMEj58T,:sckw7sHcW4KWao." + \
                      "!T_BW+0TiISJ*yrWVISqc9=gsREXS-cHg1upifwbWc6irpce:Y" + \
                      "Cexbn,1v7;uaEZu7608+NTiNrv=xKaZbc3Y?_mLYZeRtFG7?fP" + \
                      "Xnd_:uv5vnO2n8xd.mc_XSD1NA42cn.C4RK+WB_6czAykAk9pI" + \
                      "5:J2=;AIgo.-D9OKjFD6?POLzH4RsjjRH+,oA:tEOlSJBqFK+G" + \
                      "lL8w_XQ=,rqf9KA?;;UAZ=Sf55vYfNvQ?fhE_tHL76r:.pfVBG" + \
                      "w.I3aM6U,0X!sx=YezIVucu!q:9qbSAUV.AXC1qJx!+*RSDy=O" + \
                      "vxGWV*-r,?cn25.K44a.D;m*OjpHv_58IznjPaj3*,VojAqH1P" + \
                      "v*QF-NNSU_*M4,OL-Y9jYfnM;WQ6.nj0BH84jkXGrRC.GTBV;m" + \
                      "?0yetoErc6tHlZbZ9PJlbNKO5pnN,unaP?dTf6dcNyZYPfGkuH" + \
                      "HkM;_YAf:AGfc=,EeTSt*rD_Rq.s4aXwpE!;!0zWx0mnYesWQ9" + \
                      "KtKmy.oI3RIelVJHVaqfIIZ9_y0y_nD+PwO2TadVPiw7n?NsTn" + \
                      "8SVK+sRDzdrE,FCp4wYgbKH43GtpM6D_bLM!WwJc4-+r1.n2;0" + \
                      "p00NurtbhZdH?F=0?-w9pZnEWr,AGx6M?IKICSnYZE3F_Vx2Td" + \
                      "4m53;ef3r9.Yv,7BH88P_Xx+5rDmoYltaWX27s1Pd;=,!rorI_" + \
                      "g_fKRV23uE6;mpR3lKFeC5!*_hSJaR2uR8rP_9-7X89jiVsVbD" + \
                      "f*0cS7tO?LTPqx9RSxl,1q4i7;NSM=6hDb,RloygfiwCpihuGm" + \
                      "W!RUN=J!NV.g74RinCO=l!-nVphGJ_ZHq,2Xk;J9DMpA+R1wf2" + \
                      "xNaYW6!TxJQBD;??zDsODlCUIb9S?;GXiSEV;HVL=73z5rv_Q?" + \
                      "IvSbVQuQENO,L-KnU7WPa2KhtIl?_trUdZlTIjM;O0fDOXe.R_" + \
                      "oEHm+uiY-lQlSWKsBxLuFC1=8OLmt0_NO7vJ+:KBCs43fTe5DB" + \
                      "3gX7HCK7Y1l-xq!YVxxSwer_--tIZ4rok9YLLf..s7eNuIhj5f" + \
                      "I.s1NkihTKJXg5QPLhv5q6s*l2qEYKSMFc;IM5UTc_gKzqg1nW" + \
                      "+BTK5ta65Y=JDC!wJUFSV4UnnNduo!7Qam6lEi82cbp?aHgxUR" + \
                      "VnHdW7r+XOBS.Cno3dwnHg25m0JNiwV:yd9=pzl5mM4PX;zP5Q" + \
                      "EF2MKkv6nV7366pvcW0kN2SKdZ6:VzBhJ?XZDL4TK:I=i3LOw!" + \
                      "X4SAn7aDtocy3:RWDLaVtzYw+.d*KeLXVCj;7lK=a-tIEiKO:j" + \
                      "UmEcaswXoWQsjFst_zYkf_w3pw-zi+EGOMDjP0yrQ*jY?!m.+o" + \
                      "Jn=CQLvbVjdz?GbrT_QoU0rB*CFAZms2BeD:Y+wyhy;ldZQ7_j" + \
                      "RtRZlQa9AsEYIqPQFyP1f7sScRAgGfIRX9yFEo27-HNUF3C!!S" + \
                      "knN,e.rLNZP389+T:wkulw!XzzYx;QLLSIaoShG*_dLIrf1??g" + \
                      "g0l:_0usYbcOgjRYF5yU9mJZ;fRGo+4hoO7y2.w0Ji=0ulh*tX" + \
                      "-_+9LEBl9A.kXqs2A_REl;+15+ICYKbHUs.hvZJPcN0k79rKWx" + \
                      "RJ5aE2,mMdA0RRr0iIj,Kh-;?oMXYEFOk4Q=ADWaIeRP5vWouf" + \
                      "yq!v1sdapO8hh3XE6X+N.fKUqO5kxxPd2OJ_SQXuFwgzCchEWY" + \
                      "aGZpvcVF?QRHMnLXmDZiyZdvBipSfYSzs1?P.JV46dkNtr5gwO" + \
                      ":IWsqOD?TiRMxNESAx3lwP=Zv8uOYjY--RNb.ial:W+o;ERRgX" + \
                      ".34qucDunW_U2zJnbe,MHIXoeOJiyrvNLTolusr?0EJ?vxN,:h" + \
                      "eDvI:K-b-xrn1i3I4LGOFRfCr7mgzMcnq?ARayA;go6PlJ*c0c" + \
                      "2CgvyNBr5h5akDPlV,kFxY5;:;a!lB8hovtEk;gAPy+dOYcx4I" + \
                      "RHXY9UtXoacv;3CkS.laONAPP80hP.PMI8E073NMEHc3-HXa_9" + \
                      "FXIjSzRN8lk6?v3C=ndFMzWhar:ELjOCo1e;7+sO9KDjm9CQES" + \
                      "R5V9,NJaq_IH!fvRx7K.BRbwRlzvoegp38SJy53.PD63,bxCUI" + \
                      "Ha=3y2AYS1MkMn0;B13BaZPnNLI5o0*t0Ni44.0b?xtY2oyR?o" + \
                      "QUfFIhE___,0+54YNQ*KWbFeNS,S1mhnprCr4?!i+hsAL8ZkWI" + \
                      "K4XZ=oLtvofICR_ifFLlkEb!L4jtqfNpS8h37Ac8wSGD-gnT,-" + \
                      "Q2N2*.3XMsiDuW;C=sBppNLvf_wtrr,t8M=ltSFMf5qk.Ytmdt" + \
                      "lqCWTXRGov-jXP0YmTilu=;t:szfZtv_iT_xxySTLsoumB*Mfs" + \
                      "_8bu93M+O2;LLABek?26jNQ1BlptZ?P__bxO?b4n-ku6ZhuD*O" + \
                      "c;cDHx9hhv9s*xm.jIF6CJb;v9SL!0dMmb8*VOX:kuNK;P7.fJ" + \
                      "*TKlzU_snYVRD_xwKqCQecFmAnU.,:4S1xXoekMf8;uQtGY?xH" + \
                      "rpIs.WVeXHKPGxflzKS_45nFNsmF=AirVR1CpbkPNAokJ70mUk" + \
                      "b2nGW0HDZJg4*-Aozoi3I3Kn-aucf,7+oR?X9Jy=6nhg0hJmd2" + \
                      "sVGH!rQKJnqdqTSJX,oUXRNdDigWbxfgM.ASBC+M-ZYsp2yCpp" + \
                      "HWizM0;NZKd.Py8RHPpY1Q:u_ESY1wBLpG8D*e!-n;r_7ISCOr" + \
                      "KkS;BM:*WfhH=ef71zGrLZmF4u3AMjyVH0Yup,pGLmRUrsWqQ+" + \
                      "N2V.=t8M7jTEo-KymSr+yz7!J!Ek.;KyhO4m=f=S!oLI5jWsHS" + \
                      "k5Q=3llsbJBL:.L8llM1l7zI7ngj;bt*XRxzT!58*ourz5?SZu" + \
                      "wKm!wVWuJch69GC-1yXKC?C9LOmQigx9rHgQ:?uqhz*7tbZw4." + \
                      "to*?2-ZGP3cjObjeF7uMO+Y0_3L:!PCj0AE9?LwaylST4OgloT" + \
                      "=s0PyFyuj:_0PrRb,+.y*DlooishwFm.MIeZR1jfCMBlCwLl:d" + \
                      "nKo-rXViX3-AYPlu784P,vX6p:KNvbgjHk1?:AAmaOc7NJnURd" + \
                      "o9wnN9+eJaq2bDSe9M6x4UIgDJCv+4WMDxmA9p!aTnVx7S3X4j" + \
                      "JVryxks66CzJxPL96Z8hqvk.;7.L!dQL2Pp9GDE4O4sD,aZQhe" + \
                      "zxZbH.7FqK5=ptnoUy,OBjf?Aw,otQLIw6KFKIWr6hr?2mll!n" + \
                      "=aPWuYAMWch+vw*D-gWV!FN+?77OTn.m0;wF_3m7AOb582PMml" + \
                      ".*OT4_o-g8o8cz=Z3nB8*tDmMA9xyvRM6tIPU:*3THzRT7p,dM" + \
                      "z_G_,A6_KsZbDItzUKK;pMBC;QvI2aJ!RpsE=*wHt,1yhUww96" + \
                      "8Eci29+Cqz3P:n0zU1IYab_O=4C?Q5t4uN_GN5cjZcgDutCmYP" + \
                      "AUD_Mzfx=y7OTK0_E_2;z9nnf:Uu5N2p6cX-EM;i?ufWwGAhA5" + \
                      "KGH,7iKg5bjK,BxBnl6t!PUDnXdYaRCnG+R;Y8554Xz=nU61SG" + \
                      "yg5C65ijuy1U=;l9+8vvc1-w-AcKoJMd6GzGm0iU0Xa3nFiNJJ" + \
                      "y+Nr5SvBpr!8YOCnk5:r2DaBp;FuQPBhLATDQW?4R,?0r0BVYp" + \
                      "39.1MnpIj?.zQ-o0ydtgUfw,gy8B9+YIMijo3zi02X87Rh:uuJ" + \
                      "i.W+3519sHM+gt?cklSmoRl6*CC?1;QKbcpY:e9n*A-+PKu5T;" + \
                      "t56Xec,yfyP!OEJzOYu-qBds-n44SP*K8*:lptBXM?zgppV:3G" + \
                      "EHjgf82OE-.!QB;0!U6O.X+e2KYa:3gZUSoXzsgjH2rx6cydQX" + \
                      "R.4JUmT;IMoXB68Y-qYL?P_LJP_GD,ItVs=.O1nByOkhYZA9GZ" + \
                      "QJYm;xrEwRabrzCl!qIrXuKPRJ*:OE.o3JVynwvgwHf6rWIihB" + \
                      "tf=LhYU9G_ImlXhEw=TXd:hR3piry+!xuM0cS=m+:uimDH_vI3" + \
                      "I1e:XySQMw8+odz;WD?Ghn;pNb;7xOYjQKH+_Uje3YEL?F9HBb" + \
                      "rhX,KPijT_-Z.N.OombzWw=5VFBsCB_,;fVLOYLE-YJvcD4lLO" + \
                      "85dykEk?5XRqJubCo1!?a7re3nK+Sc2lQOyk=2ZLgAAV=iK8=M" + \
                      "Tu3WZW19aGm2Hce-w2mOjPZQmm=smNvoHG0t!AGvLPYx8A_9Gf" + \
                      "3j:s+siRUu!bGazVaD.+rPYKt0MkRCgQbhgKd9aIc7Y:aF0.;f" + \
                      "ErO:Ks_8TNN;te_p!KFtEiWJvLHAGBZsZI5YjEkPznC!chYq2f" + \
                      "hwboT.5+w-B=WcXtfxBf8kynC5GefjcPAXPq6LHD.Vgo:Vj*q." + \
                      "6A5wX.Mei3eJt9PB5HeH-27+d3Vv22XVg1rnyUts-!Owshc5+z" + \
                      "h5R=D:_UhCZ_;8Vv?1b_?6fj8F2tFBdssAaJZMvyW65kwZZD.3" + \
                      "WMUk=1Id2JRVW=BE5IXw+B*c_0ynBVRiOTBDMEQ4K0vZZRNodl" + \
                      "HXlTeyap,P8ND8+NusL+z7fKDVxxTxhg,X_0j8ojB,GBm;J0?L" + \
                      ",NXoZaODhmuT9DKc!Vfq=.vWLKTP;+iE,EBwJIK-9qRn*JQSuE" + \
                      "2yx!AgQOMq,!1KF3zn0DDdy8veqdlx8w6+lD8CtOLM8aQCgUxy" + \
                      "CXMYW-W*6Q1_5kt3yeIXR6PBcd2+0Qm+zy-8m;jYEYSyjo-+oN" + \
                      "e=jit?glOHwepie79vi:O;gT,.*-PvuGy0LguGRX3r;STfgHrw" + \
                      "yGnf0dzr,L79sUsfnm9KE4IiY4,Xs-S,1ZZqgKDPiPQ:uF3:*G" + \
                      "1QxL06Sw8Ye;3M.ZioN!vp+x*DT2*e.GZ::Fzf:GU1:Se2_G:p" + \
                      "r-w-9k4ub_8.L6QeNdIll.D*q9KMen*xgB,zNIrdy+Bu6ydHjh" + \
                      "JGn;d=!3QQmsRttYv6d2,VyHT2ZsrbbznuR;4frE;J2v_OS;Np" + \
                      "?ZWPs;HQr1!H-Z:6QaErs,AQ;jwSa:rPDxBjDKqDZpz!k:g!Q=" + \
                      "Df-wVzMCmi;FL1HM2!LZedvTpVq1lP4MqR+PP629Je1DysvYfn" + \
                      "FZAodyN2z=3-b.ot=WucpglAsUVLGRFdv+cvr=7Q?A?m=n!um5" + \
                      ":!.E2_1VPeoa0E+x;8M,1B+w2i;G57fw27Tr!j4AmY61k1ifY." + \
                      "XzF3PPi9f=KuGZSEPs4qzocCARZZ??:jlCNP-oacj1VrOIccbG" + \
                      "dC8k_CqBrAkswNoSbadONvyYnhoa0Y_2+Hx==4wwT=gKV3pNn;" + \
                      "CMQKi-ktj:okEi1sWs3?3kAIu3VTrdc-qIwreXdZI4ByuH8cow" + \
                      "ngf2KTt2CLH+1OrSacd_4HZRnvR2g1Zn8he1.f=HL3MYkZ7Eyi" + \
                      "nP..XLDw4A7fA.LrH1DS96vo6bN.Qew-MqMMQ=qWmq6j0-!so+" + \
                      "bMp,bXQBfmTmVS+56ie.TuW!,Tm=2Xajh6q6N*CPr8-2f7JxzS" + \
                      "=,==WFl+mhYKF9hoeypoWMcVhu8X9UvK+DCW2pyJVfwySvx1P4" + \
                      "6tLx.bp!EM:?U4YSOff0HC4+64WGxmN+xQ7m+Uejn0.bKHdYU_" + \
                      "bt4.lh8X4Evn0Zh1*tgFt-,CWi-fxmtsnQA?eM9sa7TQLI;wPU" + \
                      "umnA6CQ-mZ.TCgqdwCfm6HzUUrBhvK0kT;i;5QE?h73Cn!t67A" + \
                      "5F93TMeiQeTq7Sf-3K5q=;Z,wZDR:mi1EOTaHJz+1!jSgTW2Ct" + \
                      "7xqVsRjKMIfQ0ZTqAqEZhQ;5bk0FANTC7VqD,XZYdvBDk7HHY4" + \
                      "M-suS6QyPCnI9XVyyX_.gOE-XZ;-KJ.3Ey04s.1vcQbmqv?yVr" + \
                      "8XVb71Q:kt7T;xn4L;=RbSbV_6K8hi=xgjR-*BDWSqRArr6m9s" + \
                      "XV9o?ZVciaS!R*aUxGifi9j_9MNgio1QP,hbhwlzB-djhahFft" + \
                      "Sdgc1susd*hLu7hSf-3gwJ3m=9;=7:b+75p*VWLU+4i*bt;fww" + \
                      "J.Og2FMGbTqrq3-Ti31YPj+1S6xlxgChkb6V3h*FTfVb+a3FG9" + \
                      "vl.F.63dUngJL-MoDkG4-3gr!GSio+r9iA0EKm.mR5wo*IpN3p" + \
                      "uxRd==AFFe*DvLRZKKIi151=Rc!*0kO45KRJ*vX_3hyB5*Uw:y" + \
                      "_4??vMnZhPbL5d6trjMD-gjxT.2kjm2m50NP8b._d!vDdyqMgQ" + \
                      "tzrkqe-8,yKzA=UMozo8BMrV:+0KPvdMW,UT-acmxLCZM+ZOQa" + \
                      "e3l*i7ghB.tA,*BTeUF_d9AyA93BjwNew;sejE9r*UWTt=Eo8j" + \
                      "8QtCqHB4WA.JdMs=aj-TbqxA_Xf;==lC5pG7qnywjG-P:x?qEK" + \
                      "jwSJQ8Plcz-GgrdudwdHqDMR!Wol0Al4DeCM??kZ7R;Cs3Z9m=" + \
                      "bx.+fGj7FFGMW5y0EqHHO,jwyyIxn!Q8wRhI?;Vd!B48e+Hsci" + \
                      "HADAtS.!D8n1z6;3,jlBl02Hj9,d?T=vwWCnmlpoVxKTCKjM1;" + \
                      ",hSiQHUY?_t7VT_*J,fT7I;mi_be_!p-8?It9=asnsVV?X-9mO" + \
                      "2WnWvCbabViswlD?CTdS2z7TBjug3?Inxwb9j3cS:qUnIsx:e-" + \
                      "DAnf+Ch:*0KdmClx=?W+vmF1;g3E9M4Rxxl=?_:82gpBg6x25v" + \
                      "??R!aig5!=h_BREPD=1k,vq_9VjP,gsu.:ajGoPlsY5rueGUkR" + \
                      "ZFB;FL+yFsUdDIIDJxDXl_-GYDGLh3KgMaaDYhY00A!gn;qX.l" + \
                      "Wl;zoJ3updLze70lByRVZg3MHN-zgb3VYtG0Mw1ppoJYxseap-" + \
                      "fW8jP*xBBIE!?V9O?_lc7+fK3jXo3VlnKS85sV5_bf=:,MinML" + \
                      "BfbHSzCO8+Da9Y:8FT1Zfz.M?Os=5rQ7F6BZTQunS3*CiMLbuH" + \
                      "W5PfiSbwx:tTUXDIoz8i46sQb0XST.lehOo.QLZTE:aT3kVdiG" + \
                      "_pcfcUB74kkz,cs2vgAd*AHkUr1RkiUW4-3hBtca8M?hZnRbNg" + \
                      "UX-Tk:SUXqh119:o6UB-E*w?D_6iMIq22FIZxHN1rLzb4FzutZ" + \
                      "R-v9wa8tzpi-qN+5_Df80xq-Zg3rY5=LQqAK;:SX2.voFmYfMu" + \
                      "AOHYh0J!azFI?zjxow,H_E.3QaZdEW3.xmP.lS3.Z0.ak_Pim6" + \
                      ".c2.eac?Pp67ldxxDlK3ce0BG2qY+co:iz2GgU;tNG6ItN=u25" + \
                      "*jVCVUCh+g?;cR0APdEu0U-XG07Svf*uCjhOoAq,z+auwzI3aV" + \
                      "sZw0mL;XxI8qJIBAjsVKdC_iKlHjNE:N_C,7Be?zkxNbPQf5Yq" + \
                      "S7v5CJaODI7fLJO3STj2rTuUHE0fY;7ba!mh_nEIthKFCZLcG2" + \
                      ",fj1FGvEDZj:8IGjH_95xEObGyL!1z_iq*S6FF8M2VP66*x!gt" + \
                      "VtF;4i.9FW7Nj,pc;wSlWBu:Cls.;=6?C?.=lV!1Z3J-ws_?*f" + \
                      "G+5U*+cXiG,QtqxrnWABvM4gX4U0:4HNXOiqW?sRVwlWZ?HIt." + \
                      "to*LK!Hpj-B!nUDKDgPkU6yZhb1*bd1kT8-eagySOUoRnZU2X+" + \
                      "KMPg3=75oBKi+d6**9sCN83M84ICXW_G2y!Z-0Uamc0?SIaF,8" + \
                      "jkieEcyJ_yMXgfPjISjY:ox01A8lYeZSSDy!*pz8UE,QYxQe;:" + \
                      "dcQGm8Xgs_eP;Ink_pQRa*hr1JtyKrEs,2;8Kt5vOC!xqoI,rk" + \
                      "yuMr,Ogrrb0sVUvJf8HZV:EP75!VTaymn2!wvY7J:T,a_1zpdf" + \
                      "oNZz48VZv?zq4eMcYm31p_?hUxV=*5*S5TmwZlqJ!=,oP0+x6G" + \
                      "Q+q*kDndJPnXlJvn4Irr26qt0M=uoWkH?Rt8fBMIVW5rJA8UPG" + \
                      "Of96FGRqs54UN!?2rSOx;,-sp3WP97=QpGj9h,Xn=Rvk*h2xQd" + \
                      "sZiOQ6j;-s*bm0-wERIUWGMv;yeaTmCree08*SzXE2aVg9TtV," + \
                      "mGo7xRR7bz_ufhNZCAX_kHBBaRv270ywNS9Kc+!PTKmAem02;K" + \
                      "ri4J;fVobyboJVCU_DyP!YzFwmREjMSKdX9C8!w;gm!c5_Xy5q" + \
                      "JBlgRT.ih26E7W_DPhzKN7FufP:Y8XF,6;yVm78Y5Fm5=iTnBp" + \
                      "M7;WiczGsgT9=RqUo_1a9Q0uN?ZD.27ail!nmdSWCyTD_R*_kR" + \
                      "yr4rxrM?MO2;2FC!5VBDv437Xr2*JDNsbv;*BTliBGgZicvtE+" + \
                      "qure015-7MsS,KH,tOdvZQBfu8z1*FWNewffV2w3ftmEGggPld" + \
                      "T4O5nEHst;tB2Y7!vxy*?ZUxe40!dQ+z2S3FLI+_hDSh3L*oKv" + \
                      "y8LMejv-MhM.?D3192DVx.CN8AmayLN8sUpqphbs3ZT;N*Asnx" + \
                      "oMpR:RXgVtob==5oLQ2_Uq?94mMqI!p5QP97:1JpTId_A._F7D" + \
                      ":LErSLJ9dbL-HgcW_5O2xMZ65sVvgM9zVEY84-skeg1VOHn;mz" + \
                      "0e+b-7WKTyzX5tjR3atOLzL*1ywjE78SOUy4E3ReD*vs4sp.ok" + \
                      "S?!rqcD4Vasf4V-XRQ8qGk1Ao5D15Un.qL9.g,n:uvCZG6y-1u" + \
                      "wf*FfnJ4aZ_CLnyVi5Gk4ALw8HM=yYowAc,wZ8.d0EfXbvK2qM" + \
                      "Mk4v915MCNSwpW=oc.hnK2bC2:*ezXExSPie-aVa3.VoqDzu?y" + \
                      "L5FWHPH1:zzus?72WGlxzJJQte_7B6:.w1beu!0R+r+wscK8r:" + \
                      "kDEoOg*hS._Kz15ALR:2!p4Ac*.hnuigbi8V=;m7wsJAk?1QMM" + \
                      "kc.400YQ2_*TE;V_luJcsMK.YD-8yb228p?tm1odvSrWu:kQiT" + \
                      "?wmnCRyDBZF9Hkcas=r=Jvko6PSIaVOlCLltxU7ok,P_;FgSPu" + \
                      "*_C.50!,nWo9:NcKY,mQrR6Z,DV!bAc:NdSdDseWM,-2bfGnqb" + \
                      "mC+?N9P5K4.v_pi?f+kRb62IQEoePB8:my.GVK3c;c7NE9+peR" + \
                      "=Cgqnd5.MG+0p-FsW3xcJbTHLHAOO*Hp6:zJ,hs9pzHIR7f0:S" + \
                      "LRY+Daw8sCl+5wfLMvUInBzn?sDdtge:-Qj?k2qigdRzsk61i=" + \
                      "zGWSym;a7xE7,=pg4O!+OBdXMVoQm81-4GG6?rZYg9SUow_BRe" + \
                      "M!0saI1jpZRKoo,RecEe9ytHi86ODCKw_DigL!xirhSH-=99wZ" + \
                      "hSQ.pMLJq,4D93n5GUcccz2bI;j.ERV+:-1va4Z?EzKgd-3WEU" + \
                      "FR;:V9Pk_JiVmgaef=?tIh4txe*N+DZu,lnkpS!uQ,+IHiAVmq" + \
                      "5_+sDpNh-hciBR1:qJth+oN_bSFoO!FJ0C.nU;6x+oe.7Jvf?X" + \
                      "ao_22mvSLH1F*XCx,je3t,*H3SIB;mziTgX!l68H:k8ld3pAPW" + \
                      "*lh5hyXWoRog5;In5th;K5,tn0MxPYZJ,m9NW0Fs.6yuc_z6uS" + \
                      "gmEFk,2mK5WwU6vQ5;OjvVVXFS5;mW;b?2hEv7HlR*l;hKeg.t" + \
                      "PiNM8nIoxE+Vzc!i,tZEJ7U55+klR;I0sJ4!Hr;-Xs7=v6JpYe" + \
                      "jYsorh*sX_w-ih+ZBO3PFM=hAG0Rlz2mSo0NFdfG_MLPvVvqC6" + \
                      "g;UXuFWZJlqHSEj;bb295I=fNjRDmM2PM-IDSgDRTQgxEQElYj" + \
                      "?!EY?v;bfAY*U80=0yH,NEa*1!si.I;Q5Eeg,kub.:_ttLADF=" + \
                      "cx_eY!rX?1G1-_=tyiuZyzK3QnX?GSbns;4HMNJ4TBjvp2DOns" + \
                      "gRI5ns+VQ7ZWDVpFiWv9RJIL2UeqOT,+O=2zzqd3trKZN0zR48" + \
                      "0CexFT35S.wPz_J.q;7g6aBuUTW1Uxjwolc:+O9Ocda75zaZ,." + \
                      "QHo_X;*YNd2*nXB=MzTBIqyt+AkdeJ5FWNJE;2!Mh9uF?mx53p" + \
                      "fDD5jup8PrOQhFzVe:R50BBK4B+bqZfRT.,fvJf,,zhBe.TOSA" + \
                      "ZsB4svcwRVfrr8W+x.6OgSxykhhxlarl=jWZBL0Hq1U4O23Lo;" + \
                      ".seQ6LpFbkwUlQ0W-_dRzD2OZ8*v=X3xan6mpv3N0c8LjR:UF+" + \
                      "Y;6Z8!pT_;MVSPCxA8tf.Qo*JppWvh?EuWT*54vCIOWDPsh250" + \
                      "CEjA5k,TRTWZwkdcGx+A=S+6L3d.u:27VLvZNgelyHv!5yKuv4" + \
                      "h?vBM0GH9qmj4R;P32znCN:!RlR8+dKpPQSLYT9BUfN_iUZ9UR" + \
                      "k*F7W6:9R;BGUE=:VTXk.tS+Y:6wanVuE::+ARnJ;zys!,XIsA" + \
                      ",pj*C+erBGXjEVXme!Crx98bF4Frp.=6j_asznEICsIKZcRBx0" + \
                      "!rgqy1Q3oF+vO7OlgWipq.SM3MGuqASy?t_U_AvL1Og9Xykzos" + \
                      "7T6NrhA1juznqH8+icxX9eSR4.qO2z6LiPq0k0hubGBEEVKPSE" + \
                      "kds_nn8KP-be9;NfjX=eayl5RgT=6WgdvnKrE*Jt!epEJXdJyj" + \
                      "UIqxZyylQ.Za!Looh-,P+r*9BTrux=_e+oTiGzOBXqM=PrWBo?" + \
                      "dzJD01WA_.e4eNgykHGgn*Y;aMRbXyuf2+I?x5zODS=.UOHv=c" + \
                      "qeQ3b=bF0GS;Z0wgvBva9Uc-S_WGd3TK*N*ML?A0HzigwZi?gn" + \
                      "CoYkWj64s.V:cQ2z_cyo,0;LIW02r3:kR2wWqoX;mFMIMl+WBq" + \
                      "oW-T+3smka7xI8Fy?VQy:1WX9r30CAgQ8gZ6Mr6krF6KuYcMo!" + \
                      "e41FnjM8eAr_:7UoxNQ7ql_BVGOXn7=rIFJqTVeIj.Fe+drI7k" + \
                      "wJsWP_l;0!JKiIz;;:-WiJVna9sdv4vYsHz0q,Q4JGzRYF9z8L" + \
                      "8jgaXv=;khrc2N74RHdmJU,1K,!ZJf,ob12ZCG9nZM2?3h33!s" + \
                      "+J4g-rVvd9y4I1PepK0mPJ;tvq-r-LHL7MEFZxXBlJNxH6RSFo" + \
                      "Jrf.hJ6,VX;jl44K,nUOkZR=C?tw,oGoTfKRi:nXon4hnDD_oP" + \
                      "u9z-02sI9QmFjtIU=Vg_p?:Mf+,7:OV*c?h-llC2,4Xv2_r=as" + \
                      "S2wRAl2U68Cb8ofh6_*Ph-!o9VC0j6L8C33GJpdkilBLzxF+:i" + \
                      "!jZwv:E_s8*6j=uC_8uRvItwdJ*IZFYcH_z=uH+W2l=!:g1D72" + \
                      "6bUFCv17iPmgze+h+_MnJxQp-iCiK?8uBz.LCXvg-SxK+Xga1o" + \
                      "7luvFpCPG:GsF,p2KFnV.J!;gHfReLERiFN!I4X0!OsqgJjzHH" + \
                      "1DS8-ZXzV19dreS3ZtAO5GVGjSn1lpUTr_;oxA:nJcH0Re,825" + \
                      "Gfvu!1jR9.qeG!fcLws_xtWw!Uqof3_0D_qP1_7xV8BV.E5zMZ" + \
                      "3i1uYg-pKjMAk0M0OTd02EC29:p,u-XQaNGvvQHRptR++!_rB9" + \
                      "fiEx6,lV.LBAy3a-lvidHV:WYK-tD=K!k;a-Ub6X.8J:yf.hv_" + \
                      "60EaOs=!EYCm=DUq,dTK,QLZQ6z!lfByEycW.zbY56T0,npk2i" + \
                      "sRLqTkv_SfW76-QxO+ri87*nyhy,DyBMZUemHhaN2f0,iW5R5v" + \
                      "u5RA4Q?:Lq?yDAWOzMwWcjAoJC2Xo!fo:D=AgY2QQ1bS9a:odW" + \
                      "scN9VbSkjsAy9,aF:;!8x?Q4aeXnEyOmI2O+Nj5yHH+J*aSXUe" + \
                      "N.J,zJSgJ:JvPbtdeHOsaNqkxvYXNzf0zENo:MksewgAcq7*MV" + \
                      "koROmW.r?IG0X7bEL!rW?amkyif5woo9=Oy.!oakV1a3quoO_z" + \
                      "L1PVvZY=NtJGAneBP2Szizy400YuH54K.jFDL-pWTgpSX*ZNk9" + \
                      ",cFes3SFr.rhU7Dg1lY,D=k=UURT5yyU0BL;Djg3e2mEWrKB,u" + \
                      "?ky2MNr-ZX_uxlQ=Csu__A8:7:Cu-Iz0jHXHg_iD8gzQGKCI0K" + \
                      "dQOJeMvINJGv,MlMFkjke3DuGDRKvJvlgQ?jAmf27n_+bZIt4W" + \
                      ".dBT*aFmBGz?B.gKj,=dGLBMdaNLaST_GHj4-e0G9sY6!60aNX" + \
                      "g*ApKU5;zsVoy7_Y9Wl:!mgJukU:y+Co0eEzs9NZ291dL_1?DZ" + \
                      "rY!qn=upnuy,::fW!0suy12!H5kX0pA.5buu8Dn*lBGKwiaPj*" + \
                      "3jAHD7Ux3zVh91;yaFtR2F+zdsuN!=p0GK84xtCiHBxp75oUDK" + \
                      ":SeN8HzS!;KDQkzwHzrwxbjOslI3GHq;97!pxmnR=-ZeuqIkz," + \
                      "8u7bI;dvMVUDaU9BRLqSAMq_SpcohQWpfFHaNwQo;MvB_BZD7Z" + \
                      "dY_0RqjDhnK?Ri7rJx_h?+nKgKvfA9Q!bQw6g?Tb2eiyB9y5gO" + \
                      "0H*M7k72gTMh85a8g;mrGPTCzLdqp;qo8nY6R4S1*_wmI_U?hP" + \
                      "f,;bb=KMoz4FD-zzesxT6oJ9?tSaP,AgrDSy_R:0va75P1gQ+." + \
                      "gx5eSD?,=XHhJfyL7xIf.S7x-03ddrdG6rIfRuP9.CJ7uCVBvI" + \
                      "_zxHcKomyHqBZcpVL1Ua+_t=,NwS0u5;2;Uj5WW;RnyPw2t9Sl" + \
                      "owFMfyAAUpk2YEOPSQr34=1.l0F,Xy8ZD2xVljA;Pb*myOmo-f" + \
                      "YhsN=:fU,fIB?3DKcHm8Acce9ykjH5pNWC!cab1asn8tZA4l.Y" + \
                      "698rpj7M0H:N7HVGbgXYlwJ6B,ZX=-2N3jc7oQP?xSMZd-;*iP" + \
                      "yV.wL9U:J8X1GhTqFqp0_j4J02sW,z5!ua!5AG+mg0pBJb:G?M" + \
                      "JLCgDYAr;NHMFp;A5gkThPp=cI,3fOY3U?XqCB3V.gRX1eah=a" + \
                      "BfK!PN3Lm6UuIN6:bg*oa61;hw+xGjOSfGx+BM=YSdydsO._.5" + \
                      "bjeA*kHru:7+XsSayJD_c:fq9_,qn-k;XM.vwlbb5RhEyH?bli" + \
                      "nAOpnnYZqENQI?!Un=zb2ibMtTqo+hFWu0Whm3?ii2oQXLWFsP" + \
                      "iZM;3=?IDRA*u*Vzx6WMRt9gapp1:k4C-uJo_b;uR-Z0hImaQa" + \
                      "4XD!h0WA_TATbjZAD+DTN:q8rWNmiEWuyzr7p5VC7rVBP8xyO*" + \
                      "oBcbF7*:CL:!UgdGaN;dp:O6BZ-c3k.5TZ3w:-veHdrIHfvOwl" + \
                      "WQOyRNkZ;diXlDiw.t_VV3nLlgE093J?paYoaZ;S!+Df_Ice:0" + \
                      "JP:wGPtu*-h8k?P?czUq3oQ._QrFe7foBoBpf_JZp?RgJ2=*IQ" + \
                      "-SOctbIA7rB*xZx3HXaHyn:E_XsL:xI-5GjqLe5,=xhx;xmB9v" + \
                      "5b_fh?UTJQRz4yr2hIZgubuAzQsHRzs9c;iaU95RBOI2bGMT5t" + \
                      "6_Q4uXIa.g!3AiRkCV8JW0R8p+-OSelMY;-2r,N5UMOKCDsEvI" + \
                      "34t*XXiNo2at-!sSXf*uf9LMr5ro8e4!cOM-xdi8YkugnDjA9M" + \
                      "ruKrNNqqD?6FWyVpJy=r+1FYTJ7:1Rkhh_9iX_Sa!T!:A1cTKz" + \
                      "BHKMLJQCc+331kccWJMupzerlrT_KN0sBp:niAzeDC+_gBhG+x" + \
                      "zI?,RasQrmehGA8s1XhHNwK4a8QPk8KcpUi;i+1Ky_:1lmzPm8" + \
                      "x8l-XgRfs62.-nv7drLuafL9EBCaAzJL6qb;sBp17.Z_+5yY*d" + \
                      "bOXMmLPLHTI_Gxa:CRcqniRggtA:K,r1pOVg4:uO0SSV*7uA2E" + \
                      "NJH-.p*.cb-5WHVupS*LOqDSlmNMr*w!FoLLyh56eKNac+5d8N" + \
                      "w5Xm2D=CcvR3t0TmHHZpw,MylTB0.LSqK.ao+stox+xfRCmgbY" + \
                      ",bJfkki8Tb-E5*OaiM?OV;VDIVE38IOlazqo0wEEuwLcKKuuTe" + \
                      "ePlpd_wteaLBIsbNp9M14fB8SLCFGDDklqMLcJUjcyaL3t+_ud" + \
                      "VzHBbwOcns_iVXeE.h5SPS!5wg7_:XNgBb14hNIZD+r+inilS0" + \
                      "8g!LYXBQxYsg?9EbW49PALXClsLc4;LmS5Fx*MEyonMZtiFsle" + \
                      "?Y:KI,XRUxZ*4yIHn9zj:wb*D4Nd9Ay6wf0?*y;YSuKw,kxg!t" + \
                      "3O9Da?RlNW0q-FE,Ma+HuKJQQJ_S1N.jlPUM0QFMF8XCHvE?01" + \
                      "d;C;wI4Mvf8T-KxOX5l8cUwfg.VAgSzt-3P?aXzSw_Ei_Pzf!q" + \
                      "JDz-zndh0DHz;NWrdY9kBLdVG**:DjN!sG6RfmuIA04-XVERbU" + \
                      "LaxY4F1RCIpy.nzCH!*,vNkBqXaBM,FQ-cU;8,r9_q8B4RlkxH" + \
                      "KckCbQ4M;Cqsc1nUKvX3ey5-zSYcRQE2ht?179;Nt1cHsD.AaV" + \
                      "WOwOB2sdq.MYAx=J6__;psH6ro9UCmDyO76P7z4ilDkWYRcNc6" + \
                      "B3+_z955-.HEbxU=zDlqZYn8Is6z:-xWS2Pz2oP84OQp!o;sZ9" + \
                      "gVXPFrO?r3dHJSFZ;.LFm4y?9h:eaz2r_zv!G?*X5PnovmsPjC" + \
                      "AKKRcc;*rxP0x,W,l:3efIF1z;dwDz=qkN9b*8FU1;moKEfA9P" + \
                      "tj6j_?IY34UY8h7K9o616E1Ubdv.go,J_kYdTIBKj,.Ik73swZ" + \
                      "ERGTaF6wO7;ImRr1HLNdVQd8g.CeBSA=QEB8A*2GWgbzyzVtLV" + \
                      "s:YGucd!9dWyvm+*feCk0tqbvjltxh.F.f+H+.ydRfPB=d?:hC" + \
                      "pbDceSQK.xABag:q:AeowzfoF08QzF7?*A?h4,B146E=J9qm2s" + \
                      "*OueZj_Hg+fJknBb.eT6GyKZQ6Of3.TUvH:m8byiv68x4.l.jK" + \
                      "43Y+Ts3n1UGtC+p?nXg18uObxp?_zhUs;UtYSVniHQM;cq5vcz" + \
                      "LrdItT0*6iEZ8ZNO3=-Yfb4k2jOrbJgxWGbko=ET;PGcxO;Xt2" + \
                      "lD56FXZ56XL.=TkJhc:,fLl=ccijkNkKQZ;LA-80NHcADRX7nW" + \
                      "Y:=0Zz9*4;9SXqXFa:69Pa8RT.;JUVcI+Kd*.1oTf0+8UfJSOL" + \
                      "-JWe-08U4PaA*u4NBFUNhvw=;Xg!?1d*z3Z-d:SeU*RnVckjzl" + \
                      "3RCT=Yv0yd;e;UwsnzUVMGAnMwpEnVzLCIrp14b:DST_cQIQSG" + \
                      "EV9B=39bQOvu8V:uj!!w.g;IgC6:OAvT4X!COwDLhvPkZO,dHu" + \
                      "+A6K1PqflCeKvSJIulpi=EDzKp.ilg.I8txEs9;FCmc2U0qXq9" + \
                      "Jhbc9YpMNW9symxkO*:K14,XKrqyIWo!*E!D1;H0_Q5vdJV1Np" + \
                      "=n4_opXp,mEKB?IeqOgplvP4GPxmtjbZi*qvL6WdPD33Kra*qm" + \
                      ":FXIWXuktlFSP.-A;A7uEtltUS8CaeF2yALZ_w!7o2KB:3!V8u" + \
                      "JUt06o9g+9eve8hGLDWXXE*yK!81.6YtF_34*JpY3rUsrDtYNQ" + \
                      "BR.LgbN:5JjEdkTmZJ2.!-T+NLQ+WhhHgaHX1Ct-!C;KH0-JlN" + \
                      ",3.B9,hAQEyhyG5drF-b4jKvt7:;R=a7v3eK-!313DwRcD-l1r" + \
                      "b=wIo4l63C3rKYfc5cT1LV,zzBVTW,pPxEN2;PoCr,KMZ-k915" + \
                      "iW.2UjZr-DdFm0g!t3L:m*nVIyS4K45oabOM:Rmq1z7AN4o1!F" + \
                      "Q_egGr8jSL-o=oyl:06*=LNK:TzH4;!uMi=:o+f;-skBS1Lbd2" + \
                      "JZ=_+3QHzeXYPFgWYJMg6lk+Qkn,s*IuGSn65UFC5G*iOFP*.9" + \
                      "Pbxd-_t4,2Bik8M;.s0SLZ=8*KpSHTqqsKoFCs,YS;B6R-sNKn" + \
                      "j20*QKE,Go3I?hvm-PiL:ADAbk?V97-hnqlF-dI*PVjbJQH0q0" + \
                      "zOVazHH?_!9dVTHljMe,.K7plK2RnBd*Bla:PL*z;F:XGtv;X9" + \
                      "=XaZzSR,H8yd-9wcV-nF8Wjcr*b4d1l3Z3+sxcwEk2jcZcIkDm" + \
                      "NB_lNQJmp*PZHVo-hO_70M,PGZNX91g;SsrEYh_0,cn+Z01!0w" + \
                      "LM?GNbBtP?w:0iBWovUm*=;F98=1q_Z8:evH*XMCbtwoNC5wck" + \
                      ";!X8zxm,k;6;dmYuLSmQmPjyx,F2JwegJ4PqV3rTq5hwX-xFIo" + \
                      "ToIMI9kbgfmVQ?ckPpa5i?BwGlRSnkCLo.RVh;DiVDlC-+kmHt" + \
                      "YUG0I6jB24L1kqSIuFvo*Y5:Ma9n8zxFY!Wd!z1d-C,-*Puro3" + \
                      "A0jkk8extuOwS5k.EZG?6tbfFSP--J*32J;:TayJVT*F7;Qm7K" + \
                      "gAzo5ua3D0nKfp:wr_cQ1.RR:?Z!oMThK05pH5Rno:hkl9MeqJ" + \
                      "5-?6tAnGE9zkGOgkHH4y5no4bK-.f.++3R8IZTMxgJ4tb4O1k2" + \
                      "a5OM+VpfnPC+4Ab9-8IuKPLaCzZzb-t2xILf*A7X2WHo5zr7mH" + \
                      "QNjKhKcZ;VGCFh0n2JSG4Ko.zNtb;0+_WFR_g;L:1dF5LBD-uS" + \
                      "Xl,*P5TI;K_bpG9eLntr5;gW._eXI.gd9aK,0O6-AwX__3!=qe" + \
                      "cLlBEqV8CKIsmRE!H1n=EIQ-3,u7ZfX-JuqXenE4Rr4z.39zZ3" + \
                      "q6S1VhGK*t*v54Gd3e7-ggqk3ZN+6?Tk6;WxI21lxw=UOO-M9*" + \
                      "sEwIuv4cOzHkhJullRYX4uJdvaKX:H0M3u_Je87i:kBQBH*LHB" + \
                      "FQ+sUXJpM:N*_dlgrho8,6!fJ=rU.eHigZotkW4a==EJz6JDR." + \
                      "Xwf;FFtsq:=3ZzaA+Uw*0hfdbUX=fieS=lMc!XMkOApo,izxK;" + \
                      "vvpRi6M?b.!=O-5_d81eklUCi3zKfWa9+g0LfrHt1gops-DrPf" + \
                      "lMs0d!.Kda.E:Wb83OIXQd*0!nv?gzsCB8:orh9rdFHO089AF7" + \
                      "hNqSO,qupXy=JBaSDO;mn+dVdZt?*i7-1nr6ndc03dq.=ma8J+" + \
                      "UHl1gKUAZSyQt+Q28QApS;xYRsZ35TV1X2.w;wuXrrJFWBqsMB" + \
                      "dGrCu15K=fXZ?J?Xyi*+8z4W_2SBjzKgyi*T8Db91xP8:H*7To" + \
                      "Ik6VG1thHMwY7Wu92G0OtK?OyNxAgDWOPRE1is;Fm5t,gPNGd=" + \
                      "Pb:EO3hwZF-2mWLWevEvwm=CXXMWbZI8h1PUea,=ZEkG7qy4je" + \
                      "fVluQCmeNdc5_a8IW3gov+GxYT7EB+6qWk2Ph,AR8Gwtm;r!MZ" + \
                      "l7-tSdo=*uHio1JX-!GV-,61aCSSj1oIyDV_U*Fkc4trK-,9CG" + \
                      "D_p5ytJ8.3h=lV*FWf2y*69ku:n_oYX1;P=XHXK37j0z.ZbAzZ" + \
                      "j8xYoWMT+Us;kBpAxcE7Y.YvjGjq=AV91RxqBhF5d98V,1Ch.=" + \
                      "pWSUvY!If9z7;*KGSlYX8POZUAF57Vi;-Uwf9Cak11uN2lON_m" + \
                      "=Uz*GELLODp?;wuE-U3+Aa-P.2ZG!th94=J1Tgoq__VZ3gB3bW" + \
                      "bqD1FJZbS;1nS+O!masOZaLRh+i92XngejD=xGb-4ZZzp!m1yc" + \
                      "RJJwHi,DN0GjJfO7s1k8x!=oAVXwIla;SA4qdc=WsMn0di6vMg" + \
                      "ClxDK3Xu0*!eKL=v3VwhyNOFxX7yU7_f_5ho_a*Q-XVrnqAT1q" + \
                      "r6:*3NP4fN,7,8KML-i4cfaR!mcyuz9I89!!PRhahfudtZsi2y" + \
                      "t0Rc*89=R_*1QoM=!0svJZXpV4ph;e8NbH*u_6rgdq*d6u+SJb" + \
                      "bG*EncU6=34A7cW:m0o*c;EI0aS*Lpp2Orw5j;nZS=,:hc0a?S" + \
                      "BBvkuZ!wGLpdTmvImLWK,3aC,firnW?+GszaDP1Sp3kA*-IgAU" + \
                      "WB:5j9RZ,C9qVz4IOttogZP5LkIJPjECD1iAWMWiZ,N7nmQNKX" + \
                      "3FsWG9ShGs=QTXEgjbVVCIY3.PCCiZ?=xTkDkJo6ylpr!-+ncA" + \
                      "L1NcfKtL7jKX4R1pzaI1c3q,C5k55T10PIv4KN-Bg4Oi2,PAma" + \
                      "4-ywE6N:D=JEKn3iqF0nLv5.;bRThK-m6eWO7NuexeI2uFUd4z" + \
                      "_;w?e0f5!;!dCKvv!FBjat+P8k;fFyiVv;_S5NBU+PR9.:u-D6" + \
                      "f=*ahkrQrR3+qI1Ax_8BhUyDwhKKRBwZPqg9d_qxmsNNf3=-W1" + \
                      "iY56ng+=?CfU4ShLUHZfanEmE!=s8PbUcTQ-2e4w9LlrDuiliH" + \
                      "k1P4jrj8r;Fi.jTIVELy:sREneCFQJNsyQc.V.TqA_+ARBitcN" + \
                      "ZO:oDl+S2LMJ=HM5+q-X*1CdOClAMgikA9So30jI6PR6mkNB!z" + \
                      "GC=69fubcKXT:Oc,NqE!fFldt;nFw56r4X:yFlY?I9;5E4c*z=" + \
                      "w_Jb_b_7FSvRM!UcDwGZjFp65-K9tchVu=sgryo-05r?nvz;=s" + \
                      "PSRufE?TfMuQfd+nOdswQZSQLzCxZC59pc+lPgZ3NxFLQF+mW1" + \
                      "W7iVOt_q_FUjtpQrzueg?cpPT4A+OEmEfqRL8Hz=qWC!KeK6O?" + \
                      "J*Ns2OXRAaJKw9.uh*hYa4!OY2B*oV_2yBXXJ.PK=vA0JWRaAt" + \
                      "kuj_zrb4IHK1h3P=z1d4stHcLJqLUv7-M74Ag0cjNnMuF2NXV+" + \
                      "bgi!F+DvqIDoGB7rhoPCBe5wJ_p!;R?9O;CDyGHrGFreW7Ac67" + \
                      "RYoun7sbo95rJP=Ekukid-Gn3aBO,z3BahgJ7PNEAa2RZz3k0j" + \
                      "oHjDo6pNhn;Lo07i_K1nDA?4Eu;wI?ZwZQHHxLn029AqMvEIhK" + \
                      "HHsoa*La=GW=a-Ihd;kil;KFp!tB*!=l?u8*aPD06Mmxa-qEDg" + \
                      "u8HwanDwN9kRH;lBgNe+-2H0IQ,yWRsFSAG4b9hdre0pCxw796" + \
                      "QfbUZ9XoUepqVf=4uMa6j!bJuWC5PngEX=xbz9=3i=zlI?7ojY" + \
                      "IC2TTwsz.D4+s0LvmLTp8T6X_YU-3r7zwzI4Sqgjbb=7JQ*kZw" + \
                      "oJ*ufD+MyaXER_MRT1;vnXxU_drF*gU==UmhOv=+xt28Q_bVCQ" + \
                      "ZRxt?YFCasi03sZKQd3qOap*tFZZSwu;Kpu;q=WaxRy-d+8dKy" + \
                      "f7sG4O6*wNXRwlVvv??ICE9.a!CY8RXMP3ZP1IcJxma7:8FD:E" + \
                      "Uu-ZVnZCOPE4VR**3yys_oP?xTaRv-qQbRpddr1ld?yccKoik;" + \
                      "Tf=.nyY0vjzdI2zuw-PBr8sJb.e3x5YQyRVp1v6xAA2JycGsy-" + \
                      "Ci7UGoHDcwVf1zhyY=AyCkB:uVhibZvS.lIlV_rUoClk?FEVs?" + \
                      "=5M9Qb,4G.fV1kVvpzxU=IN?oNJnMiBDpT!lShe8AI4rLogGzq" + \
                      "!5OkP,6G7fUtRyAHrqHZ9-2cSRyzHD49m4lNw5NWoHOUa6?zMm" + \
                      "9,gWcfV9?WhCPp3DWbVG?0+Qqv.wjWEX4vt?SLHeZUm26KJpn," + \
                      "xWyv7g5jcQMcgOlZiyvH+yPQf9ejphm!8emtnK?-,z;ZjXN-DF" + \
                      "kxN8k0QgURPx1?H8;NovlTa-si*Sqvw=jVQ+oPY;epxd;?JWbw" + \
                      "c2Kn*Fy7d1mx41QK-XNYrA_EpG,pG?T9A?+K-eK7k9U4fQLE0b" + \
                      ",lH2QzBRB_lu7O6+:ObOi-tPc=vroIy=tjCiXQPKXZI52ZU5_Y" + \
                      "TG-eMD7_Gop_YvJ*eP.K5C_cpr0yN:0F386Z0vw_y?tMl4!Yi-" + \
                      "RUzBdwYnZR_c!hsfu4oX+dx.5JErj_lTluzA*alm*KRw=4-?qp" + \
                      "myzyQ,N+vdEjjK41bRp7Bu6HE.BrgkwCi8:kuUX:*4be3RYJ*+" + \
                      "IXJV5U5Q4ApDy_rpb7-!snV*5L0V8sVw1wXubJejJAkh*wDk_C" + \
                      "yraM=SfsN1a6YrdaKHt:uCnX+S1-C4"}]
# ########################################################################### #

def probe_read(args, sitename, endpoint):
    if 'XRD_NETWORKSTACK' in os.environ.keys():
        del os.environ["XRD_NETWORKSTACK"]
    if args.ipv4 and ( not args.ipv6 ):
        print 'ipv4'
        os.environ["XRD_NETWORKSTACK"] = "IPv4"
    if ( not args.ipv4 ) and args.ipv6:
        print 'ipv6'
        os.environ["XRD_NETWORKSTACK"] = "IPv6"
    if ( not sitename):
        return
    for file in CSXE_FILES:
        filename = "/store/test/xrootd/" + sitename + file['name']
        with client.File() as f:
            status, response = f.open("root://" + endpoint + "/" + \
                filename, flags=OpenFlags.READ, timeout=90)
            #if (( not status.ok ) and ( status.errno == 3011 )):
            #    status, response = f.open("root://" + endpoint + "/" + \
            #        filename, flags=(OpenFlags.READ | OpenFlags.REFRESH),
            #        timeout=180)
            if ( not status.ok ):
                host = f.get_property('DataServer')
                print host
                print(("\nopen(root://%s/%s, flags=OpenFlags.READ, time" + \
                          "out=90)\nXRootDStatus.code=%d \"%s\"\n") % \
                          (endpoint, filename, status.code, \
                          status.message.replace("\n", "")))
                publish(args, args.sttime, sitename, status.code)
                return
            import pdb; pdb.set_trace()
            host = f.get_property('DataServer')
            status, data = f.read(offset=0, size=65536, timeout=90)
            if ( not status.ok ):
                print(("\n%s\nread(offset=0, size=65536, timeout=90)\n" + \
                          "XRootDStatus.code=%d \"%s\"\n") % (filename, \
                          status.code, status.message.replace("\n", "")))
                publish(args, args.sttime, sitename, status.code)
                return
            #
            chksum = hex(zlib.adler32(data) & 0xffffffff)[2:]
            if ( chksum != file['adlr'] ):
                print(("\nblock 0 checksum mismatch, test file \"%s\", " + \
                          "adler32 is \"%s\" should be \"%s\"\n") % \
                         (filename, chksum, file['adlr']))
                publish(args, args.sttime, sitename, 10)
                return
            #
            rndm = random.randint(1, file['blck'] - 1)
            #
            status, data = f.read(offset=rndm*65536, size=65536, timeout=90)
            if ( not status.ok ):
                print(("\n%s\nread(offset=%d, size=65536, timeout=90)\n" + \
                          "XRootDStatus.code=%d \"%s\"\n") % \
                          (filename, rndm*65536, status.code, \
                           status.message.replace("\n", "")))
                publish(args, args.sttime, sitename, status.code)
                return
            #
            chk73c = CSXE_ASCII73CODE[ (zlib.adler32(data) & 0xffffffff) % 73 ]
            if ( chk73c != file['code'][rndm] ):
                print(("\nblock %d checksum mismatch, test file \"%s\"," + \
                          " adler32 code-73 is \"%s\" should be \"%s\"\n") % \
                         (rndm, filename, chk73c, file['code'][rndm]))
                publish(args, args.sttime, sitename, 11)
                return
            #
            host = f.get_property('DataServer')

            print(("\nBlock 0 and %d of file \"%s\" successfully read from " + \
                "\"%s\" and checksum of data verified\n") % (rndm, filename, host))
            publish(args, args.sttime, sitename, 0)

parser = argparse.ArgumentParser()
parser.add_argument("-V", "--version", help="show program version", action="store_true")
parser.add_argument("-4", "--ipv4", help='Use IPV4 NetStack', action="store_true")
parser.add_argument("-6", "--ipv6", help='Use IPV6 NetStack', action="store_true")
parser.add_argument("-s", "--sitename", help='Sitename')

# read arguments from the command line
args = parser.parse_args()

if __name__ == '__main__':
    while True:
        sttime = int(time.time())
        print sttime
        args.sttime = sttime
        args.ipv6 = True
        args.ipv4 = None
        probe_read(args, args.sitename, 'cmsxrootd.fnal.gov')
        args.ipv4 = True
        args.ipv6 = None
        probe_read(args, args.sitename, 'cmsxrootd.fnal.gov')
        endtime = int(time.time())
        difftime = endtime - sttime
        diffsleep = 300 - difftime
        if diffsleep > 0:
            print 'Sleep %s ' % diffsleep
            time.sleep(diffsleep)
