

//美团天天神卷+赚米粒
//百度 美团登录自己抓Token ，美团小程序首页天天赚钱
//只支持青龙
// 环境变量 mtTk （建议直接复制）
//多账号用 @
//如需关闭膨胀，环境变量 sjpz 值：false
//本次更新：增加推送，可设置膨胀。
//推送依赖 https://gitee.com/xiecoll/radish-script/raw/master/MT/sendNotify.js

//环境变量 meituanyq 优惠券邀请码

const $ = new Env('美团');

let status;
let sjpz = ($.isNode() ? process.env.sjpz : $.getdata('sjpz')) || 'false';
const notify = $.isNode() ? require('./sendNotify') : '';
status = (status = ($.getval("fhxzstatus") || "1")) > 1 ? `${status}` : ""; // 账号扩展字符
let slckArr = [],userids=[]
let meituanyq = ($.isNode() ? process.env.meituanyq : $.getdata('meituanyq')) || '';
let allMessage = '';
let time = Math.round(Date.now() / 1000)
 let mtToken = ""
let acceptTagCode, queryTagCode
let num = rand(10, 99), slcks = "",userId,uuid,inviteCode 


!(async () => {
    if (typeof $request !== "undefined") {
        fhxzck()
    } else {
       
        if (process.env.mtTk && process.env.mtTk.indexOf('@') > -1) {
            slckArr = process.env.mtTk.split('@');
            console.log(`您选择的是用"@"隔开\n`)
        } else {
            slcks = [process.env.mtTk]
        };
        Object.keys(slcks).forEach((item) => {
            if (slcks[item]) {
                slckArr.push(slcks[item])
            }
        })
        console.log(slckArr)
        console.log(`-------------共${slckArr.length}个账号-------------\n`)

        await qswcdl();

        await notify.sendNotify(`美团天天神卷+赚米粒`, `${allMessage}`, '')

    }
})()
    .catch((e) => $.logErr(e))
    .finally(() => $.done())


function qswcdl(timeout = 0) {
    return new Promise((resolve) => {
        let url = {
            url: 'https://luobook.coding.net/p/code.json/d/luobook/git/raw/master/code.json',
            headers: ``,
        }
        $.get(url, async (err, resp, data) => {
            try {

                data = JSON.parse(data);
                console.log('脚本状态' + data.msg1)
                allMessage += '\n脚本状态' + data.msg1;
              
                    for (let k = 0; k < slckArr.length; k++) {
                        $.message = ""
                        mtToken = slckArr[k]
                        $.index = k + 1;
                         if(meituanyq==''){
                            inviteCode=`NnOIp-QOs8SiYF1dcSlL5r8phPrCf6qkH7evMyjIoureqol0OXXaopfjjblE0yPgN86y4RcZwmbDNeilsjadKKx8C_xcAtb9biugMRpa1nHJplwNd25nXQxgtWHn9006X_TBXSsJXEvvpgsevw4IOO1GodOJn4IOG_sQpdLKzqo`
                        }else{
                            if(k==0){
                                inviteCode=`NnOIp-QOs8SiYF1dcSlL5r8phPrCf6qkH7evMyjIoureqol0OXXaopfjjblE0yPgN86y4RcZwmbDNeilsjadKKx8C_xcAtb9biugMRpa1nHJplwNd25nXQxgtWHn9006X_TBXSsJXEvvpgsevw4IOO1GodOJn4IOG_sQpdLKzqo`
                            }else{
                                inviteCode=meituanyq
                            }
                        }
                        console.log(`\n开始【美团账户 ${$.index}】`)
                        allMessage += `\n开始【美团账户 ${$.index}】`;
                        await getsharecard()
                        console.log('\n【天天神卷】🧧');
                        allMessage += '\n【天天神卷】🧧';
                        await sign();
                        await $.wait(1000)
                        await clickReferralLink();
                        await $.wait(1000)
                        await gundamGrabV3();
                        await $.wait(1000)
                        await getConfig()
                        await $.wait(1000)
                        
                        await fetchcoupon()
                        await $.wait(1000)

                        // await corepage();
                        await shenquan()
                        await $.wait(1000)

                        console.log('\n【赚米粒】');
                        allMessage += '\n【赚米粒】';

                        await aggregationpage()
                        await $.wait(1000)

                        await signin()
                        await $.wait(1000)

                        await startvisittaskop()
                        await $.wait(1000)

                        await homepageicon()
                        await $.wait(1000)

                        await visittaskop()
                        await $.wait(1000)

                        await dinnersignin()
                        await $.wait(1000)

                       uuid =  randomString(64)

                        await getmtuid()

                      if(userId != undefined){
                       await getuserInfo()

                        await getUserTasks('["1fff834702"]')
                        // await getUserTasks()

                      }
                        allMessage += '\n\n';

                        $.log(`------------------任务结束------------------`)
                    }

                
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//yq链接
function getsharecard() {
    return new Promise((resolve) => {
        let url = {
            url: `https://promotion-waimai.meituan.com/invite/getsharecard?sourceId=1`,
            headers: {
                "Host": "promotion-waimai.meituan.com",
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive",
                "Cookie": `mt_c_token=${mtToken}; thirdlogin_token=${mtToken};token=${mtToken};`,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.3(0x1800032c) NetType/WIFI Language/zh_CN", "Accept-Language": "zh-cn",
            
            
            }
        }
        $.get(url, async (err, resp, data) => {
            try {
                //console.log(data);
                let result = JSON.parse(data);
                if(result.code == 0){
                    console.log(`\n美团邀请链接：${result.data.invitationUrl.match(/inviteCode=(.*)&/)[1]}`);
                   meituanyq = result.data.invitationUrl.match(/inviteCode=(.*)&/)[1]
                }

            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//fetchcoupon红包
function fetchcoupon() {
   
    return new Promise((resolve) => {
        let url = {
            url: `https://promotion-waimai.meituan.com/invite/fetchcoupon?version=8.0.14&ctype=wxapp&fpPlatform=13&app=13&initialLng=113387518&initialLat=22931265&inviteCode=${inviteCode}&isMini=1&token=` + mtToken,
            headers: { "Host": "promotion-waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208", "Referer": "https://servicewechat.com/wx2c348cf579062e56/568/page" }
        }
        $.get(url, async (err, resp, data) => {
            try {
                console.log('\n【下午茶红包】🧧');
                allMessage += '\n【下午茶红包】🧧';

                // console.log(data);
                let result = JSON.parse(data);
                console.log(result.msg);
                allMessage += '\n' + result.msg;

            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//登录受邀
function sign() {
    return new Promise((resolve) => {
        let url = {
            url: `https://mediacps.meituan.com/gundam/sign`,
            headers: {
                "Host": "mediacps.meituan.com",
                "Origin": "https://market.waimai.meituan.com",
                "Connection": "keep-alive",
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.3(0x1800032c) NetType/4G Language/zh_CN miniProgram", "Accept-Language": "zh-cn",
                "Accept-Encoding": "gzip, deflate, br",
                "Cookie": `mt_c_token=${mtToken}; thirdlogin_token=${mtToken};token=${mtToken};`,
            }
        }
        $.get(url, async (err, resp, data) => {
            try {
                // console.log(data);
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//领券
function gundamGrabV3() {
    return new Promise((resolve) => {
        let url = {
            url: `https://mediacps.meituan.com/gundam/gundamGrabV3`,
            headers: {
                "Host": "mediacps.meituan.com",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": "https://market.waimai.meituan.com",
                "Accept-Encoding": "br, gzip, deflate",
                "Cookie": `token=${mtToken};`,
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.3(0x1800032c) NetType/4G Language/zh_CN miniProgram",
                "Referer": "https://market.waimai.meituan.com/gd/single.html?el_biz=waimai&gundam_id=2KAWnD&el_page=gundam.loader&urpid=70690.163800938339.57783928.2&appkey=a144a9fa40a42c55af00214bb4bb3993971%3A14290dingdanxia0&source=wandie&_rdt=1&noguide=1&utm_term=&utm_campaign=other&utm_medium=MU&actid=2&channel=union&utm_source=60413&utm_content=1380426723950108690",
                "Content-Length": "369",
                "Accept-Language": "zh-cn"
            },
            body: `{"gundamId":20625,"grabKey":"4E35567E5DAB45E5B7CC2B3BDE2E67B7,AA41950DF11D44AA8324A7E0E32CE806,211BCD47900F43D1AAC3864049DB1400,0084BF0333F844A2846DA0827C21EBF7,34BCA492BAEA4D2E8CD0394B31D5CB26,AD317E383B064F84ACE3A8DCDC8C2572,DFEAE6C5C7664DBBB5A64E5F52297B5C,CF56C7F89ADF4933990684F91F88E4A0,5B4653A4388947249D9DEFBE53BC22E7,30941E32462A42AB9B3D741B77A96A6E","defaultGrabKey":"E28198A627324F85B4FF89FA10D093EC","actualLongitude":1133869${num},"actualLatitude":229312${num},"needTj":true,"couponConfigIdOrderCommaString":"464617074,464617087,464617110,464617124,464573157,464573265,464574741,464577259,458043537,459036220,459956075,458056972,458056406,458047734,392417289,452275501,452275388,452275365,452275482,452447814,452446826,452446582,452447692,392417317,412809091,446694745,418776149,277807308,431529548","couponAllConfigIdOrderString":"","rubikCouponKey":""}`
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log(`天天领神券:`);
                allMessage += `\n天天领神券:`;

                // console.log(data);
                let result = JSON.parse(data);
                result.data.coupons.forEach(element => {
                    console.log(`领到:${element.couponAmount}元${element.amountLimit}的${element.couponName}`);
                    allMessage += `\n领到:${element.couponAmount}元${element.amountLimit}的${element.couponName}`;

                });
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//读取邀请码
function getConfig() {
    return new Promise((resolve) => {
        let url = {
            url: `https://ihotel.meituan.com/topcube/api/toc/weixin/getConfig?url=https%3A%2F%2Fmarket.waimai.meituan.com%2Fgd%2Fsingle.html%3Fel_biz%3Dwaimai%26gundam_id%3D2KAWnD%26el_page%3Dgundam.loader%26urpid%3D70690.163795067930.57783865.2%26appkey%3Da144a9fa40a42c55af00214bb4bb3993971%253A14290dingdanxiawaimai%26source%3Dwandie%26_rdt%3D1%26noguide%3D1%26utm_term%3D%26utm_campaign%3Dother%26utm_medium%3DMU%26actid%3D2%26channel%3Dunion%26utm_source%3D60413%26utm_content%3D1380426723950108690`,
            headers: {
                "Host": "ihotel.meituan.com",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Cookie": `mt_c_token=${mtToken}; thirdlogin_token=${mtToken};token=${mtToken};`,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.3(0x1800032c) NetType/WIFI Language/zh_CN", "Accept-Language": "zh-cn",
                "Referer": "https://market.waimai.meituan.com/gd/single.html?el_biz=waimai&gundam_id=2KAWnD&el_page=gundam.loader&urpid=70690.163795067930.57783865.2&appkey=a144a9fa40a42c55af00214bb4bb3993971%3A14290dingdanxiawaimai&source=wandie&_rdt=1&noguide=1&utm_term=&utm_campaign=other&utm_medium=MU&actid=2&channel=union&utm_source=60413&utm_content=1380426723950108690",
                "Accept-Encoding": "gzip, deflate, br"
            }
        }
        $.get(url, async (err, resp, data) => {
            try {
                // console.log(data);
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//美团ttsj签到
function drawlottery(batchId) {
    return new Promise((resolve) => {
        let url = {
            url: `https://i.waimai.meituan.com/cfeplay/playcenter/batchgrabred/drawlottery`,
            body: `parActivityId=Gh1tkq-wvFU2xEP_ZPzHPQ&wm_latitude=2293${num}${num}&wm_longitude=11338${num}${num}&token=${mtToken}&batchId=${batchId}&isShareLink=true&propType=1&propId=2`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log(data);
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//美团
function corepage() {
    return new Promise((resolve) => {
        let url = {
            url: `https://i.waimai.meituan.com/cfeplay/playcenter/batchgrabred/corepage`,
            body: `parActivityId=Gh1tkq-wvFU2xEP_ZPzHPQ&wm_ctype=mtandroid&wm_latitude=2293${num}${num}&wm_longitude=11338${num}${num}&token=${mtToken}`,
            headers: { "Host": "i.waimai.meituan.com", "User-Agent": "MeituanGroup/11.9.208", "x-requested-with": "XMLHttpRequest", "content-type": "application/x-www-form-urlencoded" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log('\n天天神券 签到🧧');
                // console.log(data);
                let result = JSON.parse(data);
                // if(result.data.batchId ==undefined){
                // console.log('您已签到完毕🙏!');  
                // }else{
                let batchId = result.data.batchId
                await drawlottery(batchId)
                // }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}



//神卷
function shenquan() {
    return new Promise((resolve) => {
        let url = {
            url: `https://promotion.waimai.meituan.com/playcenter/common/v1/mycoupons/shenquan?isMini=0&ctype=iphone&isInDpEnv=0`,
            headers: {
                "Host": "promotion.waimai.meituan.com", "Content-Type": "application/json;charset=UTF-8", "Origin": "https://i.waimai.meituan.com", "Accept-Encoding": "br, gzip, deflate",
                "Cookie": `token=${mtToken};`
            }
        }
        $.get(url, async (err, resp, data) => {
            try {
                // console.log(`\n天天领神券\n`);  
                let result = JSON.parse(data);
                if (result.code == 0) {
                    console.log(`\n【神券膨胀】🧧`);
                    allMessage += `\n【神券膨胀】🧧`;

                    if (sjpz != 'false') {
                        for (let i = 0; i < result.data.length; i++) {
                            console.log(`第${i + 1}张神券：满` + result.data[i].couponOuterType + '减' + result.data[i].couponCount + ',去膨胀');
                            allMessage += `\n第${i + 1}张神券：满` + result.data[i].couponOuterType + '减' + result.data[i].couponCount + ',去膨胀';

                            let couponViewId = result.data[i].couponViewId
                            // console.log(couponViewId);
                            await multiple(couponViewId)
                            await $.wait(1000)
                        }
                        console.log(`如需关闭膨胀，环境变量 sjpz 值：false`);
                        allMessage += `如需关闭膨胀，环境变量 sjpz 值：false`;
                    } else {
                        console.log(`\n当前设置不膨胀神券`);
                        allMessage += `\n当前设置不膨胀神券`;
                    }
                } else {
                    console.log(result.msg);
                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}




//膨胀
function multiple(couponViewId) {
    return new Promise((resolve) => {
        let url = {
            url: `https://promotion.waimai.meituan.com/playcenter/common/v1/coupon/multiple?isMini=0&ctype=iphone&isInDpEnv=0`,
            headers: {
                "Host": "promotion.waimai.meituan.com", "Content-Type": "application/json;charset=UTF-8", "Origin": "https://i.waimai.meituan.com", "Accept-Encoding": "br, gzip, deflate",
                "Cookie": `token=${mtToken};`
            },
            body: `
            {"couponViewId":"${couponViewId}"}`
        }
        $.post(url, async (err, resp, data) => {
            try {
                // console.log(data);  
                let result = JSON.parse(data);
                if (result.code == 0) {
                    console.log(result.data[0].couponTitleDoc);
                    allMessage += `\n` + result.data[0].couponTitleDoc;

                } else {
                    console.log('不能再膨胀了');
                    allMessage += `\n不能再膨胀了`

                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//进入赚米粒
function aggregationpage() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/aggregationpage`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&firstInit=false&wm_dversion=8.0.3&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&waimai_sign=%2F&wm_actual_longitude=113387210&wm_actual_latitude=2293${num}${num}&userid=${userId}&user_id=${userId}&uuid=${uuid}&openIdCipher=AwQAAABJAgAAAAEAAAAyAAAAPLgC95WH3MyqngAoyM%2Fhf1hEoKrGdo0pJ5DI44e1wGF9AT3PH7Wes03actC2n%2FGVnwfURonD78PewMUppAAAADilzSKQNsGsANCcAOfkzXSyXDo0Fe7uoMaEVq9kWussZeJXc0VKjG%2B8p9BVykTVjD6llukPjRjBsA%3D%3D&open_id=oOpUI0axUjNf5hrYNu47FvHlyuyE&sdkVersion=2.17.0`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                // console.log('\进入赚米粒');      
                // console.log(data);  
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

function randomString(len=12) {
    let chars = 'abcdef0123456789';
    let maxLen = chars.length;
    let str = '';
    for (i = 0; i < len; i++) {
        str += chars.charAt(Math.floor(Math.random()*maxLen));
    }
    return str;
}

//美团赚米粒签到
function signin() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/signintask/signin`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&wm_dversion=8.0.3&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&waimai_sign=%2F&wm_actual_longitude=113387210&wm_actual_latitude=2293${num}${num}&userid=${userId}&user_id=${userId}&uuid=${uuid}&openIdCipher=AwQAAABJAgAAAAEAAAAyAAAAPLgC95WH3MyqngAoyM%2Fhf1hEoKrGdo0pJ5DI44e1wGF9AT3PH7Wes03actC2n%2FGVnwfURonD78PewMUppAAAADilzSKQNsGsANCcAOfkzXSyXDo0Fe7uoMaEVq9kWussZeJXc0VKjG%2B8p9BVykTVjD6llukPjRjBsA%3D%3D&open_id=oOpUI0axUjNf5hrYNu47FvHlyuyE&sdkVersion=2.17.0`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log('美团赚米粒签到：');
                allMessage += `\n美团赚米粒签到`;

                // console.log(data);  
                let result = JSON.parse(data);
                console.log(result.msg);
                allMessage += `\n` + result.msg;

            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//领浏览赚米粒
function startvisittaskop() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/visittaskop`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&wm_dversion=8.0.3&taskStatus=1&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&waimai_sign=%2F&wm_actual_longitude=113387210&wm_actual_latitude=2293${num}${num}&userid=${userId}&user_id=${userId}&uuid=${uuid}&openIdCipher=AwQAAABJAgAAAAEAAAAyAAAAPLgC95WH3MyqngAoyM%2Fhf1hEoKrGdo0pJ5DI44e1wGF9AT3PH7Wes03actC2n%2FGVnwfURonD78PewMUppAAAADilzSKQNsGsANCcAOfkzXSyXDo0Fe7uoMaEVq9kWussZeJXc0VKjG%2B8p9BVykTVjD6llukPjRjBsA%3D%3D&open_id=oOpUI0axUjNf5hrYNu47FvHlyuyE&sdkVersion=2.17.0`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                // // console.log('领取任务');      
                // console.log(data);  
                // let result = JSON.parse(data);

            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//点击浏览赚米粒
function homepageicon() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/aggregationpage`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&wm_dversion=8.0.3&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_visitid=892319ae-edba-45a0-8c6f-79a4f35e3116&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&req_time=1637953453523&waimai_sign=%2F&wm_actual_longitude=11338${num}${num}&wm_actual_latitude=22931290&userid=13558869&user_id=13558869&lch=1089&sessionId=LH8Q16&optimusCode=20&riskLevel=71&partner=4&platform=13&uuid=${uuid}&openIdCipher=AwQAAABJAgAAAAEAAAAyAAAAPLgC95WH3MyqngAoyM%2Fhf1hEoKrGdo0pJ5DI44e1wGF9AT3PH7Wes03actC2n%2FGVnwfURonD78PewMUppAAAADilzSKQNsGsANCcAOfkzXSyXDo0Fe7uoMaEVq9kWussZeJXc0VKjG%2B8p9BVykTVjD6llukPjRjBsA%3D%3D&open_id=oOpUI0axUjNf5hrYNu47FvHlyuyE&rc_app=4&rc_platform=13&wm_uuid_source=client&sdkVersion=2.17.0&source=21&firstInit=true&rank_list_id=13465b7b017e8b52e4c248f38c01d1d4&ref_list_id=13465b777107af42e498988f38c01d1d&wm_ctype=wxapp`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                let result = JSON.parse(data);
                console.log('当前米粒：' + result.data.user_points.valid_points);
                allMessage += `\n当前米粒：` + result.data.user_points.valid_points;

                console.log(result.data.user_points.subtitle);
                allMessage += `\n` + result.data.user_points.subtitle;


            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//浏览赚米粒 5
function visittaskop() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/visittaskop`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&wm_dversion=8.0.3&taskStatus=3&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&waimai_sign=%2F&wm_actual_longitude=113387210&wm_actual_latitude=2293${num}${num}&userid=${userId}&user_id=${userId}&uuid=${uuid}&sdkVersion=2.17.0`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log('\n领取浏览任务奖励：');
                allMessage += `\n领取浏览任务奖励：`

                let result = JSON.parse(data);
                if (result.code == 0) {
                    console.log(`领取成功`);
                    allMessage += `\n领取成功`

                } else {
                    console.log(`不可重复领取`);
                    allMessage += `\n不可重复领取`
                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}
function getmtuid() {
    return new Promise((resolve) => {
        let url = {
            url: `https://open.meituan.com/user/v1/info?fields=id%2Cusername%2Cavatartype%2Cavatarurl%2Cnickname%2Cemail%2Ccity%2Ccityid%2Cmobile%2CisBindedMobile`,
            headers: {
                "token": mtToken,
            }
        }
        $.get(url, async (err, resp, data) => {
            try {
                let result = JSON.parse(data);
                 userId = result.user.id
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}
//执行任务
function getuserInfo() {
    return new Promise((resolve) => {
        let url = {
            url: `https://web.meituan.com/web/user/points?token=${mtToken}&userId=${userId}`,
        }
        $.get(url, async (err, resp, data) => {
            try {
                // console.log(data);
                let result = JSON.parse(data);
                
                    console.log('\n当前金币：', result.data.count);
                    allMessage += `\n当前金币：` + result.data.count
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//三餐领米粒
function dinnersignin() {
    return new Promise((resolve) => {
        let url = {
            url: `https://wx.waimai.meituan.com/weapp/v1/wlwc/dinnersignin/sign`,
            body: `wm_dtype=iPhone%2011%3CiPhone12%2C1%3E&wm_dversion=8.0.3&taskStatus=3&wm_dplatform=ios&wm_uuid=${uuid}&wm_longitude=11338${num}${num}&wm_latitude=2293${num}${num}&wm_appversion=7.8.8&wm_logintoken=${mtToken}&userToken=${mtToken}&waimai_sign=%2F&wm_actual_longitude=113387210&wm_actual_latitude=2293${num}${num}&userid=${userId}&user_id=${userId}&uuid=${uuid}&sdkVersion=2.17.0`,
            headers: { "Host": "wx.waimai.meituan.com", "Connection": "keep-alive", "content-type": "application/x-www-form-urlencoded", "wm-ctype": "wxapp", "Accept-Encoding": "gzip,compress,br,deflate", "User-Agent": "MeituanGroup/11.9.208" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log('\n任务：三餐领米粒');
                allMessage += `\n任务：三餐领米粒`



                let result = JSON.parse(data);
                if (result.code == 0) {
                    console.log('领取成功，当前米粒：' + result.data.current_points);
                    allMessage += `\n领取成功，当前米粒：` + result.data.current_points

                } else {
                    console.log(result.msg);
                    allMessage += `\n` + result.msg

                }

            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}


//去浏览60秒
function getUserTasks(tasks='["495070b239","176f400a8f","672129ff6d","320ffa53e7","6ccbda387f","6f2d5f144f","075eb403be","563983d5f1"]') {
    return new Promise((resolve) => {
        let url = {
            url: `https://cube.meituan.com/topcube/api/toc/task/getUserTasks`,
            body: `{"userId":"${userId}","userType":"MEI_TUAN","uuid":"${uuid}","cityId":1,"taskIdKeys":${tasks},"sourceType":"MEI_TUAN","mini_program_token":"${mtToken}","inviter":"","inviterTaskIdKey":""}`,
            headers: { "Content-Type": "application/json" }
        }
        $.post(url, async (err, resp, data) => {
            try {
                console.log('\n任务：天天赚钱💴');
                allMessage += `\n任务：天天赚钱💴`
                // console.log(data);
                let result = JSON.parse(data);
                if (result.code == 0) {

                    for(let item of result.data) {
                        if(item.code == 0) {
                            if(!item.taskRuleVos || item.taskRuleVos.length == 0) continue;
                            if(item.title.indexOf('小程序下单') > -1) continue;
                            let isSignTask = item.extend ? true : false
                            if(isSignTask && item.extend.isSignInToday==1) {
                                console.log(`\n任务:${item.title} --- 已完成`)
                                continue;
                            }
                            for(let tasks of item.taskRuleVos) {
                                if(tasks.status == 'PRIZE_SUCC') {
                                    console.log(`\n任务:${item.title} --- 已完成`)
                                } else if(tasks.status == 'CAN_RECEIVE') {

                                    console.log(`\n任务:${item.title} --- 可领取奖励`)
                                    await $.wait(1000)
                                    await sendTaskPrize(item.taskIdKey,tasks.taskRuleIdKey,0,item.taskNo,tasks.taskRuleNo)
                                    if(isSignTask) break;
                                } else {
                                    console.log(`\n任务:${item.title} --- 未完成`)
                                    await $.wait(1000)
                                    await startUserTask(item.taskIdKey,tasks.taskRuleIdKey,123)
                                    if(isSignTask) break;
                                }
                            }
                        } else {
                            console.log(`\n任务:${item.title} --- ${item.msg}`)
                        }
                        await $.wait(1000)
                    }

                } else {
                    console.log(result.msg);
                    allMessage += `\n` + result.msg

                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//执行任务
function startUserTask(taskIdKey, taskRuleIdKey) {
    let bodys = `{"openid":"","userId":"${userId}","cityId":"20","mini_program_token":"${mtToken}","uuid":"${uuid}","userType":"MEI_TUAN","taskIdKey":"${taskIdKey}","taskRuleIdKey":"${taskRuleIdKey}","cubePageId":123,"sourceType":"MEI_TUAN","riskForm":"e30="}`
    return new Promise((resolve) => {
        let url = {
            url: `https://cube.meituan.com/topcube/api/toc/task/startUserTask`,
            headers: { "Content-Type": "application/json" },
            body: bodys
        }
        $.post(url, async (err, resp, data) => {
            try {
                // console.log(data);
                let result = JSON.parse(data);
                if (result.code == 0) {
                    await $.wait(1000)
                    await updateUserTask(taskIdKey, taskRuleIdKey, result.taskNo, result.taskRuleNo, result.actionNo)

                } else {
                    console.log('\n任务：', result.msg);
                    allMessage += `\n任务：` + result.msg
                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//执行任务
function updateUserTask(taskIdKey, taskRuleIdKey, taskNo, taskRuleNo, actionNo) {
    return new Promise((resolve) => {
        let url = {
            url: `https://cube.meituan.com/topcube/api/toc/task/updateUserTask`,
            headers: { "Content-Type": "application/json" },
            body: `{"openid":"","userId":"${userId}","cityId":"20","mini_program_token":"${mtToken}","uuid":"${uuid}","userType":"MEI_TUAN","taskIdKey":"${taskIdKey}","taskRuleIdKey":"${taskRuleIdKey}","taskNo":"${taskNo}","taskRuleNo":"${taskRuleNo}","actionNo":"${actionNo}","cubePageId":10000003,"sourceType":"MEI_TUAN","riskForm":"e30="}`
        }
        $.post(url, async (err, resp, data) => {
            try {
                // console.log(data);
                let result = JSON.parse(data);
                if (result.code == 0) {
                    await $.wait(1000)
                    await sendTaskPrize(taskIdKey, taskRuleIdKey, result.taskNo, result.taskRuleNo, result.actionNo)

                } else {
                    console.log('\n任务：', result.msg);
                    allMessage += `\n任务：` + result.msg
                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}

//执行任务
function sendTaskPrize(taskIdKey,taskRuleIdKey,cubePageId,taskNo,taskRuleNo) {
    return new Promise((resolve) => {
        let url = {
            url: `https://cube.meituan.com/topcube/api/toc/task/sendTaskPrize`,
            headers: {"token":mtToken,"Content-Type": "application/json" },
            body: `{"userId":${userId},"userType":"MEI_TUAN","mini_program_token":"${mtToken}","uuid":"${uuid}","cityId":20,"taskIdKey":"${taskIdKey}","taskRuleIdKey":"${taskRuleIdKey}","taskNo":"${taskNo}","taskRuleNo":"${taskRuleNo}","cubePageId":0,"riskForm":"e30="}`
        }         
        $.post(url, async (err, resp, data) => {
            try {
                // console.log(data);
                let result = JSON.parse(data);
                if (result.code == 0) {
                    console.log('\n任务领取：', result.msg);
                    allMessage += `\n任务领取：` + result.msg

                } else {
                    console.log('\n任务领取：', result.msg);
                    allMessage += `\n任务领取：` + result.msg
                }
            } catch (e) {
                $.logErr(e, resp);
            } finally {
                resolve()
            }
        }, 0)
    })
}



function rand(min, max) {
    return parseInt(Math.random() * (max - min + 1) + min, 10);
}

function Env(t, e) { class s { constructor(t) { this.env = t } send(t, e = "GET") { t = "string" == typeof t ? { url: t } : t; let s = this.get; return "POST" === e && (s = this.post), new Promise((e, i) => { s.call(this, t, (t, s, r) => { t ? i(t) : e(s) }) }) } get(t) { return this.send.call(this.env, t) } post(t) { return this.send.call(this.env, t, "POST") } } return new class { constructor(t, e) { this.name = t, this.http = new s(this), this.data = null, this.dataFile = "box.dat", this.logs = [], this.isMute = !1, this.isNeedRewrite = !1, this.logSeparator = "\n", this.encoding = "utf-8", this.startTime = (new Date).getTime(), Object.assign(this, e), this.log("", `\ud83d\udd14${this.name}, \u5f00\u59cb!`) } isNode() { return "undefined" != typeof module && !!module.exports } isQuanX() { return "undefined" != typeof $task } isSurge() { return "undefined" != typeof $httpClient && "undefined" == typeof $loon } isLoon() { return "undefined" != typeof $loon } isShadowrocket() { return "undefined" != typeof $rocket } toObj(t, e = null) { try { return JSON.parse(t) } catch { return e } } toStr(t, e = null) { try { return JSON.stringify(t) } catch { return e } } getjson(t, e) { let s = e; const i = this.getdata(t); if (i) try { s = JSON.parse(this.getdata(t)) } catch { } return s } setjson(t, e) { try { return this.setdata(JSON.stringify(t), e) } catch { return !1 } } getScript(t) { return new Promise(e => { this.get({ url: t }, (t, s, i) => e(i)) }) } runScript(t, e) { return new Promise(s => { let i = this.getdata("@chavy_boxjs_userCfgs.httpapi"); i = i ? i.replace(/\n/g, "").trim() : i; let r = this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout"); r = r ? 1 * r : 20, r = e && e.timeout ? e.timeout : r; const [o, h] = i.split("@"), n = { url: `http://${h}/v1/scripting/evaluate`, body: { script_text: t, mock_type: "cron", timeout: r }, headers: { "X-Key": o, Accept: "*/*" } }; this.post(n, (t, e, i) => s(i)) }).catch(t => this.logErr(t)) } loaddata() { if (!this.isNode()) return {}; { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), i = !s && this.fs.existsSync(e); if (!s && !i) return {}; { const i = s ? t : e; try { return JSON.parse(this.fs.readFileSync(i)) } catch (t) { return {} } } } } writedata() { if (this.isNode()) { this.fs = this.fs ? this.fs : require("fs"), this.path = this.path ? this.path : require("path"); const t = this.path.resolve(this.dataFile), e = this.path.resolve(process.cwd(), this.dataFile), s = this.fs.existsSync(t), i = !s && this.fs.existsSync(e), r = JSON.stringify(this.data); s ? this.fs.writeFileSync(t, r) : i ? this.fs.writeFileSync(e, r) : this.fs.writeFileSync(t, r) } } lodash_get(t, e, s) { const i = e.replace(/\[(\d+)\]/g, ".$1").split("."); let r = t; for (const t of i) if (r = Object(r)[t], void 0 === r) return s; return r } lodash_set(t, e, s) { return Object(t) !== t ? t : (Array.isArray(e) || (e = e.toString().match(/[^.[\]]+/g) || []), e.slice(0, -1).reduce((t, s, i) => Object(t[s]) === t[s] ? t[s] : t[s] = Math.abs(e[i + 1]) >> 0 == +e[i + 1] ? [] : {}, t)[e[e.length - 1]] = s, t) } getdata(t) { let e = this.getval(t); if (/^@/.test(t)) { const [, s, i] = /^@(.*?)\.(.*?)$/.exec(t), r = s ? this.getval(s) : ""; if (r) try { const t = JSON.parse(r); e = t ? this.lodash_get(t, i, "") : e } catch (t) { e = "" } } return e } setdata(t, e) { let s = !1; if (/^@/.test(e)) { const [, i, r] = /^@(.*?)\.(.*?)$/.exec(e), o = this.getval(i), h = i ? "null" === o ? null : o || "{}" : "{}"; try { const e = JSON.parse(h); this.lodash_set(e, r, t), s = this.setval(JSON.stringify(e), i) } catch (e) { const o = {}; this.lodash_set(o, r, t), s = this.setval(JSON.stringify(o), i) } } else s = this.setval(t, e); return s } getval(t) { return this.isSurge() || this.isLoon() ? $persistentStore.read(t) : this.isQuanX() ? $prefs.valueForKey(t) : this.isNode() ? (this.data = this.loaddata(), this.data[t]) : this.data && this.data[t] || null } setval(t, e) { return this.isSurge() || this.isLoon() ? $persistentStore.write(t, e) : this.isQuanX() ? $prefs.setValueForKey(t, e) : this.isNode() ? (this.data = this.loaddata(), this.data[e] = t, this.writedata(), !0) : this.data && this.data[e] || null } initGotEnv(t) { this.got = this.got ? this.got : require("got"), this.cktough = this.cktough ? this.cktough : require("tough-cookie"), this.ckjar = this.ckjar ? this.ckjar : new this.cktough.CookieJar, t && (t.headers = t.headers ? t.headers : {}, void 0 === t.headers.Cookie && void 0 === t.cookieJar && (t.cookieJar = this.ckjar)) } get(t, e = (() => { })) { if (t.headers && (delete t.headers["Content-Type"], delete t.headers["Content-Length"]), this.isSurge() || this.isLoon()) this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient.get(t, (t, s, i) => { !t && s && (s.body = i, s.statusCode = s.status), e(t, s, i) }); else if (this.isQuanX()) this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => e(t)); else if (this.isNode()) { let s = require("iconv-lite"); this.initGotEnv(t), this.got(t).on("redirect", (t, e) => { try { if (t.headers["set-cookie"]) { const s = t.headers["set-cookie"].map(this.cktough.Cookie.parse).toString(); s && this.ckjar.setCookieSync(s, null), e.cookieJar = this.ckjar } } catch (t) { this.logErr(t) } }).then(t => { const { statusCode: i, statusCode: r, headers: o, rawBody: h } = t; e(null, { status: i, statusCode: r, headers: o, rawBody: h }, s.decode(h, this.encoding)) }, t => { const { message: i, response: r } = t; e(i, r, r && s.decode(r.rawBody, this.encoding)) }) } } post(t, e = (() => { })) { const s = t.method ? t.method.toLocaleLowerCase() : "post"; if (t.body && t.headers && !t.headers["Content-Type"] && (t.headers["Content-Type"] = "application/x-www-form-urlencoded"), t.headers && delete t.headers["Content-Length"], this.isSurge() || this.isLoon()) this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, { "X-Surge-Skip-Scripting": !1 })), $httpClient[s](t, (t, s, i) => { !t && s && (s.body = i, s.statusCode = s.status), e(t, s, i) }); else if (this.isQuanX()) t.method = s, this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, { hints: !1 })), $task.fetch(t).then(t => { const { statusCode: s, statusCode: i, headers: r, body: o } = t; e(null, { status: s, statusCode: i, headers: r, body: o }, o) }, t => e(t)); else if (this.isNode()) { let i = require("iconv-lite"); this.initGotEnv(t); const { url: r, ...o } = t; this.got[s](r, o).then(t => { const { statusCode: s, statusCode: r, headers: o, rawBody: h } = t; e(null, { status: s, statusCode: r, headers: o, rawBody: h }, i.decode(h, this.encoding)) }, t => { const { message: s, response: r } = t; e(s, r, r && i.decode(r.rawBody, this.encoding)) }) } } time(t, e = null) { const s = e ? new Date(e) : new Date; let i = { "M+": s.getMonth() + 1, "d+": s.getDate(), "H+": s.getHours(), "m+": s.getMinutes(), "s+": s.getSeconds(), "q+": Math.floor((s.getMonth() + 3) / 3), S: s.getMilliseconds() }; /(y+)/.test(t) && (t = t.replace(RegExp.$1, (s.getFullYear() + "").substr(4 - RegExp.$1.length))); for (let e in i) new RegExp("(" + e + ")").test(t) && (t = t.replace(RegExp.$1, 1 == RegExp.$1.length ? i[e] : ("00" + i[e]).substr(("" + i[e]).length))); return t } msg(e = t, s = "", i = "", r) { const o = t => { if (!t) return t; if ("string" == typeof t) return this.isLoon() ? t : this.isQuanX() ? { "open-url": t } : this.isSurge() ? { url: t } : void 0; if ("object" == typeof t) { if (this.isLoon()) { let e = t.openUrl || t.url || t["open-url"], s = t.mediaUrl || t["media-url"]; return { openUrl: e, mediaUrl: s } } if (this.isQuanX()) { let e = t["open-url"] || t.url || t.openUrl, s = t["media-url"] || t.mediaUrl; return { "open-url": e, "media-url": s } } if (this.isSurge()) { let e = t.url || t.openUrl || t["open-url"]; return { url: e } } } }; if (this.isMute || (this.isSurge() || this.isLoon() ? $notification.post(e, s, i, o(r)) : this.isQuanX() && $notify(e, s, i, o(r))), !this.isMuteLog) { let t = ["", "==============\ud83d\udce3\u7cfb\u7edf\u901a\u77e5\ud83d\udce3=============="]; t.push(e), s && t.push(s), i && t.push(i), console.log(t.join("\n")), this.logs = this.logs.concat(t) } } log(...t) { t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(t.join(this.logSeparator)) } logErr(t, e) { const s = !this.isSurge() && !this.isQuanX() && !this.isLoon(); s ? this.log("", `\u2757\ufe0f${this.name}, \u9519\u8bef!`, t.stack) : this.log("", `\u2757\ufe0f${this.name}, \u9519\u8bef!`, t) } wait(t) { return new Promise(e => setTimeout(e, t)) } done(t = {}) { const e = (new Date).getTime(), s = (e - this.startTime) / 1e3; this.log("", `\ud83d\udd14${this.name}, \u7ed3\u675f! \ud83d\udd5b ${s} \u79d2`), this.log(), (this.isSurge() || this.isQuanX() || this.isLoon()) && $done(t) } }(t, e) }
