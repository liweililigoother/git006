// nat64自动填充proxyip，无需且不支持proxyip设置
import { connect } from "cloudflare:sockets";
const WS_READY_STATE_OPEN = 1;
let userID = "86c50e3a-5b87-49dd-bd20-03c7f2735e40";
const cn_hostnames = [''];

// =================  SERVERS CONFIGURATION START =================
// Main CDNIP for single-node links. Using the user's primary requested IP.
let CDNIP = 'ProxyIP.US.CMLiussss.Net';

// Existing TLS servers
const all_tls_servers = [
    { address: 'usa.visa.com', port: '443' },
    { address: 'myanmar.visa.com', port: '8443' },
    { address: 'www.visa.com.tw', port: '2053' },
    { address: 'www.visaeurope.ch', port: '2083' },
    { address: 'www.visa.com.br', port: '2087' },
    { address: 'www.visasoutheasteurope.com', port: '2096' },
];

// Existing Non-TLS servers
const original_non_tls_servers = [
    { address: 'www.visa.com', port: '80' },
    { address: 'cis.visa.com', port: '8080' },
    { address: 'africa.visa.com', port: '8880' },
    { address: 'www.visa.com.sg', port: '2052' },
    { address: 'www.visaeurope.at', port: '2082' },
    { address: 'www.visa.com.mt', port: '2086' },
    { address: 'qa.visamiddleeast.com', port: '2095' },
];

// User-provided new Non-TLS servers
const user_ips = [
    'ProxyIP.US.CMLiussss.Net',
    '104.17.218.234',
    '104.19.30.17',
    '104.18.79.24',
    '104.16.27.226',
    '104.17.66.10',
    'yg1.ygkkk.dpdns.org'
];
const user_ports = ['8080', '8880', '2052', '2082', '2086', '2095'];

const user_non_tls_servers = [];
for (const ip of user_ips) {
    for (const port of user_ports) {
        user_non_tls_servers.push({ address: ip, port: port });
    }
}

// Combine all non-TLS servers
const all_non_tls_servers = [...original_non_tls_servers, ...user_non_tls_servers];
// =================  SERVERS CONFIGURATION END =================


export default {
  /**
   * @param {any} request
   * @param {{uuid: string}}
   * @param {any} ctx
   * @returns {Promise<Response>}
   */
  async fetch(request, env, ctx) {
    try {
      userID = env.uuid || userID;
      const upgradeHeader = request.headers.get("Upgrade");
      const url = new URL(request.url);
      if (!upgradeHeader || upgradeHeader !== "websocket") {
        const url = new URL(request.url);
        switch (url.pathname) {
          case `/${userID}`: {
            const vlessConfig = getvlessConfig(userID, request.headers.get("Host"));
            return new Response(vlessConfig, {
              status: 200,
              headers: {
                "Content-Type": "text/html;charset=utf-8",
              },
            });
          }
		  case `/${userID}/ty`: {
			const allServers = [...all_non_tls_servers.map(s => ({...s, tls: false})), ...all_tls_servers.map(s => ({...s, tls: true}))];
			const tyConfig = gettyConfig(userID, request.headers.get('Host'), allServers);
			return new Response(tyConfig, {
				status: 200,
				headers: {
					"Content-Type": "text/plain;charset=utf-8",
				}
			});
		}
		case `/${userID}/cl`: {
			const clConfig = getclConfig(userID, request.headers.get('Host'), all_non_tls_servers, all_tls_servers);
			return new Response(clConfig, {
				status: 200,
				headers: {
					"Content-Type": "text/plain;charset=utf-8",
				}
			});
		}
		case `/${userID}/sb`: {
			const sbConfig = getsbConfig(userID, request.headers.get('Host'), all_non_tls_servers, all_tls_servers);
			return new Response(sbConfig, {
				status: 200,
				headers: {
					"Content-Type": "application/json;charset=utf-8",
				}
			});
		}
		case `/${userID}/pty`: {
			const ptyConfig = gettyConfig(userID, request.headers.get('Host'), all_tls_servers.map(s => ({...s, tls: true})));
			return new Response(ptyConfig, {
				status: 200,
				headers: {
					"Content-Type": "text/plain;charset=utf-8",
				}
			});
		}
		case `/${userID}/pcl`: {
			const pclConfig = getclConfig(userID, request.headers.get('Host'), [], all_tls_servers);
			return new Response(pclConfig, {
				status: 200,
				headers: {
					"Content-Type": "text/plain;charset=utf-8",
				}
			});
		}
		case `/${userID}/psb`: {
			const psbConfig = getsbConfig(userID, request.headers.get('Host'), [], all_tls_servers);
			return new Response(psbConfig, {
				status: 200,
				headers: {
					"Content-Type": "application/json;charset=utf-8",
				}
			});
		}
		case `/${userID}/allnodes`: {
			const allServers = [...all_non_tls_servers.map(s => ({...s, tls: false})), ...all_tls_servers.map(s => ({...s, tls: true}))];
			const vlessLinks = generateVlessLinks(userID, request.headers.get("Host"), allServers);
			return new Response(vlessLinks, {
				status: 200,
				headers: {
				"Content-Type": "text/plain;charset=utf-8",
				},
			});
		}
          default:
            if (cn_hostnames.includes('')) {
            return new Response(JSON.stringify(request.cf, null, 4), {
              status: 200,
              headers: {
                "Content-Type": "application/json;charset=utf-8",
              },
            });
            }
            const randomHostname = cn_hostnames[Math.floor(Math.random() * cn_hostnames.length)];
            const newHeaders = new Headers(request.headers);
            newHeaders.set("cf-connecting-ip", "1.2.3.4");
            newHeaders.set("x-forwarded-for", "1.2.3.4");
            newHeaders.set("x-real-ip", "1.2.3.4");
            newHeaders.set("referer", "https://www.google.com/search?q=edtunnel");
            const proxyUrl = "https://" + randomHostname + url.pathname + url.search;
            let modifiedRequest = new Request(proxyUrl, {
              method: request.method,
              headers: newHeaders,
              body: request.body,
              redirect: "manual",
            });
            const proxyResponse = await fetch(modifiedRequest, { redirect: "manual" });
            if ([301, 302].includes(proxyResponse.status)) {
              return new Response(`Redirects to ${randomHostname} are not allowed.`, {
                status: 403,
                statusText: "Forbidden",
              });
            }
            return proxyResponse;
        }
      }
      return await handlevlessWebSocket(request);
    } catch (err) {
      /** @type {Error} */ let e = err;
      return new Response(e.toString());
    }
  },
};

async function handlevlessWebSocket(request) {
  const wsPair = new WebSocketPair();
  const [clientWS, serverWS] = Object.values(wsPair);

  serverWS.accept();

  const earlyDataHeader = request.headers.get('sec-websocket-protocol') || '';
  const wsReadable = createWebSocketReadableStream(serverWS, earlyDataHeader);
  let remoteSocket = null;

  let udpStreamWrite = null;
  let isDns = false;
  
  wsReadable.pipeTo(new WritableStream({
    async write(chunk) {

      if (isDns && udpStreamWrite) {
        return udpStreamWrite(chunk);
      }
      
      if (remoteSocket) {
        const writer = remoteSocket.writable.getWriter();
        await writer.write(chunk);
        writer.releaseLock();
        return;
      }

      const result = parsevlessHeader(chunk, userID);
      if (result.hasError) {
        throw new Error(result.message);
      }

      const vlessRespHeader = new Uint8Array([result.vlessVersion[0], 0]);
      const rawClientData = chunk.slice(result.rawDataIndex);
      
      if (result.isUDP) {
        if (result.portRemote === 53) {
          isDns = true;
          const { write } = await handleUDPOutBound(serverWS, vlessRespHeader);
          udpStreamWrite = write;
          udpStreamWrite(rawClientData);
          return;
        } else {
          throw new Error('UDP代理仅支持DNS(端口53)');
        }
      }

      async function connectAndWrite(address, port) {
        const tcpSocket = await connect({
          hostname: address,
          port: port
        });
        remoteSocket = tcpSocket;
        const writer = tcpSocket.writable.getWriter();
        await writer.write(rawClientData);
        writer.releaseLock();
        return tcpSocket;
      }

      function convertToNAT64IPv6(ipv4Address) {
        const parts = ipv4Address.split('.');
        if (parts.length !== 4) {
          throw new Error('无效的IPv4地址');
        }
        
        const hex = parts.map(part => {
          const num = parseInt(part, 10);
          if (num < 0 || num > 255) {
            throw new Error('无效的IPv4地址段');
          }
          return num.toString(16).padStart(2, '0');
        });
        const prefixes = ['2602:fc59:b0:64::'];
        const chosenPrefix = prefixes[Math.floor(Math.random() * prefixes.length)];
        return `[${chosenPrefix}${hex[0]}${hex[1]}:${hex[2]}${hex[3]}]`;
      }

      async function getIPv6ProxyAddress(domain) {
        try {
          const dnsQuery = await fetch(`https://1.1.1.1/dns-query?name=${domain}&type=A`, {
            headers: {
              'Accept': 'application/dns-json'
            }
          });
          
          const dnsResult = await dnsQuery.json();
          if (dnsResult.Answer && dnsResult.Answer.length > 0) {
            const aRecord = dnsResult.Answer.find(record => record.type === 1);
            if (aRecord) {
              const ipv4Address = aRecord.data;
              return convertToNAT64IPv6(ipv4Address);
            }
          }
          throw new Error('无法解析域名的IPv4地址');
        } catch (err) {
          throw new Error(`DNS解析失败: ${err.message}`);
        }
      }

      async function retry() {
        try {
          const proxyIP = await getIPv6ProxyAddress(result.addressRemote);
          console.log(`尝试通过NAT64 IPv6地址 ${proxyIP} 连接...`);
          const tcpSocket = await connect({
            hostname: proxyIP,
            port: result.portRemote
          });
          remoteSocket = tcpSocket;
          const writer = tcpSocket.writable.getWriter();
          await writer.write(rawClientData);
          writer.releaseLock();

          tcpSocket.closed.catch(error => {
            console.error('NAT64 IPv6连接关闭错误:', error);
          }).finally(() => {
            if (serverWS.readyState === WS_READY_STATE_OPEN) {
              serverWS.close(1000, '连接已关闭');
            }
          });
          
          pipeRemoteToWebSocket(tcpSocket, serverWS, vlessRespHeader, null);
        } catch (err) {
          console.error('NAT64 IPv6连接失败:', err);
          serverWS.close(1011, 'NAT64 IPv6连接失败: ' + err.message);
        }
      }

      try {
        const tcpSocket = await connectAndWrite(result.addressRemote, result.portRemote);
        pipeRemoteToWebSocket(tcpSocket, serverWS, vlessRespHeader, retry);
      } catch (err) {
        console.error('连接失败:', err);
        serverWS.close(1011, '连接失败');
      }
    },
    close() {
      if (remoteSocket) {
        closeSocket(remoteSocket);
      }
    }
  })).catch(err => {
    console.error('WebSocket 错误:', err);
    closeSocket(remoteSocket);
    serverWS.close(1011, '内部错误');
  });

  return new Response(null, {
    status: 101,
    webSocket: clientWS,
  });
}

function createWebSocketReadableStream(ws, earlyDataHeader) {
  return new ReadableStream({
    start(controller) {
      ws.addEventListener('message', event => {
        controller.enqueue(event.data);
      });
      
      ws.addEventListener('close', () => {
        controller.close();
      });
      
      ws.addEventListener('error', err => {
        controller.error(err);
      });
      
      if (earlyDataHeader) {
        try {
          const decoded = atob(earlyDataHeader.replace(/-/g, '+').replace(/_/g, '/'));
          const data = Uint8Array.from(decoded, c => c.charCodeAt(0));
          controller.enqueue(data.buffer);
        } catch (e) {
        }
      }
    }
  });
}

function parsevlessHeader(buffer, userID) {
  if (buffer.byteLength < 24) {
    return { hasError: true, message: '无效的头部长度' };
  }
  
  const view = new DataView(buffer);
  const version = new Uint8Array(buffer.slice(0, 1));
  
  const uuid = formatUUID(new Uint8Array(buffer.slice(1, 17)));
  if (uuid !== userID) {
    return { hasError: true, message: '无效的用户' };
  }
  
  const optionsLength = view.getUint8(17);
  const command = view.getUint8(18 + optionsLength);

  let isUDP = false;
  if (command === 1) {
    // TCP
  } else if (command === 2) {
    isUDP = true;
  } else {
    return { hasError: true, message: '不支持的命令，仅支持TCP(01)和UDP(02)' };
  }
  
  let offset = 19 + optionsLength;
  const port = view.getUint16(offset);
  offset += 2;
  
  const addressType = view.getUint8(offset++);
  let address = '';
  
  switch (addressType) {
    case 1: // IPv4
      address = Array.from(new Uint8Array(buffer.slice(offset, offset + 4))).join('.');
      offset += 4;
      break;
      
    case 2: // 域名
      const domainLength = view.getUint8(offset++);
      address = new TextDecoder().decode(buffer.slice(offset, offset + domainLength));
      offset += domainLength;
      break;
      
    case 3: // IPv6
      const ipv6 = [];
      for (let i = 0; i < 8; i++) {
        ipv6.push(view.getUint16(offset).toString(16).padStart(4, '0'));
        offset += 2;
      }
      address = ipv6.join(':').replace(/(^|:)0+(\w)/g, '$1$2');
      break;
      
    default:
      return { hasError: true, message: '不支持的地址类型' };
  }
  
  return {
    hasError: false,
    addressRemote: address,
    portRemote: port,
    rawDataIndex: offset,
    vlessVersion: version,
    isUDP
  };
}

function pipeRemoteToWebSocket(remoteSocket, ws, vlessHeader, retry = null) {
  let headerSent = false;
  let hasIncomingData = false;
  
  remoteSocket.readable.pipeTo(new WritableStream({
    write(chunk) {
      hasIncomingData = true;
      if (ws.readyState === WS_READY_STATE_OPEN) {
        if (!headerSent) {
          const combined = new Uint8Array(vlessHeader.byteLength + chunk.byteLength);
          combined.set(new Uint8Array(vlessHeader), 0);
          combined.set(new Uint8Array(chunk), vlessHeader.byteLength);
          ws.send(combined.buffer);
          headerSent = true;
        } else {
          ws.send(chunk);
        }
      }
    },
    close() {
      if (!hasIncomingData && retry) {
        retry();
        return;
      }
      if (ws.readyState === WS_READY_STATE_OPEN) {
        ws.close(1000, '正常关闭');
      }
    },
    abort() {
      closeSocket(remoteSocket);
    }
  })).catch(err => {
    console.error('数据转发错误:', err);
    closeSocket(remoteSocket);
    if (ws.readyState === WS_READY_STATE_OPEN) {
      ws.close(1011, '数据传输错误');
    }
  });
}

function closeSocket(socket) {
  if (socket) {
    try {
      socket.close();
    } catch (e) {
    }
  }
}

function formatUUID(bytes) {
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

async function handleUDPOutBound(webSocket, vlessResponseHeader) {
  let isvlessHeaderSent = false;
  const transformStream = new TransformStream({
    start(controller) {},
    transform(chunk, controller) {
      for (let index = 0; index < chunk.byteLength;) {
        const lengthBuffer = chunk.slice(index, index + 2);
        const udpPacketLength = new DataView(lengthBuffer).getUint16(0);
        const udpData = new Uint8Array(
          chunk.slice(index + 2, index + 2 + udpPacketLength)
        );
        index = index + 2 + udpPacketLength;
        controller.enqueue(udpData);
      }
    },
    flush(controller) {}
  });

  transformStream.readable.pipeTo(new WritableStream({
    async write(chunk) {
      const resp = await fetch('https://1.1.1.1/dns-query',
        {
          method: 'POST',
          headers: {
            'content-type': 'application/dns-message',
          },
          body: chunk,
        })
      const dnsQueryResult = await resp.arrayBuffer();
      const udpSize = dnsQueryResult.byteLength;
      const udpSizeBuffer = new Uint8Array([(udpSize >> 8) & 0xff, udpSize & 0xff]);
      
      if (webSocket.readyState === WS_READY_STATE_OPEN) {
        console.log(`DNS查询成功，DNS消息长度为 ${udpSize}`);
        if (isvlessHeaderSent) {
          webSocket.send(await new Blob([udpSizeBuffer, dnsQueryResult]).arrayBuffer());
        } else {
          webSocket.send(await new Blob([vlessResponseHeader, udpSizeBuffer, dnsQueryResult]).arrayBuffer());
          isvlessHeaderSent = true;
        }
      }
    }
  })).catch((error) => {
    console.error('DNS UDP处理错误:', error);
  });

  const writer = transformStream.writable.getWriter();

  return {
    write(chunk) {
      writer.write(chunk);
    }
  };
}

// ================= DYNAMIC CONFIG FUNCTIONS START =================
// Note: These functions are refactored to be dynamic.

function generateVlessLinks(userID, hostName, servers) {
	const vlessLinks = servers.map(server => {
		if (server.tls) {
			return `vless://${userID}@${server.address}:${server.port}?encryption=none&security=tls&sni=${hostName}&fp=randomized&type=ws&host=${hostName}&path=%2F%3Fed%3D2560#TLS_${server.address}_${server.port}`;
		} else {
			return `vless://${userID}@${server.address}:${server.port}?encryption=none&security=none&fp=randomized&type=ws&host=${hostName}&path=%2F%3Fed%3D2560#NonTLS_${server.address}_${server.port}`;
		}
	}).join('\n');
	return vlessLinks;
}

/**
 * Generates a base64-encoded string of vless links.
 * @param {string} userID
 * @param {string | null} hostName
 * @param {Array<{address: string, port: string, tls: boolean}>} servers
 * @returns {string}
 */
function gettyConfig(userID, hostName, servers) {
	const vlessLinks = generateVlessLinks(userID, hostName, servers);
	return btoa(vlessLinks);
}

/**
 * Generates a Clash-meta configuration.
 * @param {string} userID
 * @param {string | null} hostName
 * @param {Array<{address: string, port: string}>} nonTlsServers
 * @param {Array<{address: string, port: string}>} tlsServers
 * @returns {string}
 */
function getclConfig(userID, hostName, nonTlsServers, tlsServers) {
    const proxies = [];

    nonTlsServers.forEach((server, i) => {
        proxies.push(`- name: NonTLS_${i}_${server.address}_${server.port}
  type: vless
  server: ${server.address.replace(/[[]]/g, '')}
  port: ${server.port}
  uuid: ${userID}
  udp: false
  tls: false
  network: ws
  ws-opts:
    path: "/?ed=2560"
    headers:
      Host: ${hostName}`);
    });

    tlsServers.forEach((server, i) => {
        proxies.push(`- name: TLS_${i}_${server.address}_${server.port}
  type: vless
  server: ${server.address.replace(/[[]]/g, '')}
  port: ${server.port}
  uuid: ${userID}
  udp: false
  tls: true
  network: ws
  servername: ${hostName}
  ws-opts:
    path: "/?ed=2560"
    headers:
      Host: ${hostName}`);
    });

    const proxyNames = [
        ...nonTlsServers.map((s, i) => `NonTLS_${i}_${s.address}_${s.port}`),
        ...tlsServers.map((s, i) => `TLS_${i}_${s.address}_${s.port}`),
    ];

    return `
port: 7890
allow-lan: true
mode: rule
log-level: info
unified-delay: true
global-client-fingerprint: chrome
dns:
  enable: false
  listen: :53
  ipv6: true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  default-nameserver: 
    - 223.5.5.5
    - 114.114.114.114
    - 8.8.8.8
  nameserver:
    - https://dns.alidns.com/dns-query
    - https://doh.pub/dns-query
  fallback:
    - https://1.0.0.1/dns-query
    - tls://dns.google
  fallback-filter:
    geoip: true
    geoip-code: CN
    ipcidr:
      - 240.0.0.0/4
proxies:
${proxies.join('\n\n')}
proxy-groups:
- name: 负载均衡
  type: load-balance
  url: http://www.gstatic.com/generate_204
  interval: 300
  proxies:
${proxyNames.map(name => `    - ${name}`).join('\n')}
- name: 自动选择
  type: url-test
  url: http://www.gstatic.com/generate_204
  interval: 300
  tolerance: 50
  proxies:
${proxyNames.map(name => `    - ${name}`).join('\n')}
- name: 🌍选择代理
  type: select
  proxies:
    - 负载均衡
    - 自动选择
    - DIRECT
${proxyNames.map(name => `    - ${name}`).join('\n')}
rules:
  - GEOIP,LAN,DIRECT
  - GEOIP,CN,DIRECT
  - MATCH,🌍选择代理`;
}

/**
 * Generates a Sing-box configuration.
 * @param {string} userID
 * @param {string | null} hostName
 * @param {Array<{address: string, port: string}>} nonTlsServers
 * @param {Array<{address: string, port: string}>} tlsServers
 * @returns {string}
 */
function getsbConfig(userID, hostName, nonTlsServers, tlsServers) {
	const outbounds = [];

	nonTlsServers.forEach((server, i) => {
		outbounds.push({
			"server": server.address,
			"server_port": parseInt(server.port, 10),
			"tag": `NonTLS_${i}_${server.address}_${server.port}`,
			"packet_encoding": "packetaddr",
			"transport": {
				"headers": { "Host": [hostName] },
				"path": "/?ed=2560",
				"type": "ws"
			},
			"type": "vless",
			"uuid": userID
		});
	});

	tlsServers.forEach((server, i) => {
		outbounds.push({
			"server": server.address,
			"server_port": parseInt(server.port, 10),
			"tag": `TLS_${i}_${server.address}_${server.port}`,
			"tls": {
				"enabled": true,
				"server_name": hostName,
				"insecure": false,
				"utls": { "enabled": true, "fingerprint": "chrome" }
			},
			"packet_encoding": "packetaddr",
			"transport": {
				"headers": { "Host": [hostName] },
				"path": "/?ed=2560",
				"type": "ws"
			},
			"type": "vless",
			"uuid": userID
		});
	});

	const outboundTags = [
        ...nonTlsServers.map((s, i) => `NonTLS_${i}_${s.address}_${s.port}`),
        ...tlsServers.map((s, i) => `TLS_${i}_${s.address}_${s.port}`),
    ];

	const sbConfig = {
		"log": { "level": "info", "timestamp": true },
		"outbounds": [ { "tag": "select", "type": "selector", "default": "auto", "outbounds": ["auto", ...outboundTags] },
		...outbounds,
		{ "tag": "direct", "type": "direct" },
		{
			"tag": "auto", "type": "urltest", "outbounds": outboundTags,
			"url": "https://www.gstatic.com/generate_204", "interval": "1m", "tolerance": 50
		}
		],
		// ... a lot of static sing-box config ...
		"dns": {
			"servers": [
			  { "tag": "proxydns", "address": "tls://8.8.8.8/dns-query", "detour": "select" },
			  { "tag": "localdns", "address": "h3://223.5.5.5/dns-query", "detour": "direct" },
			  { "tag": "dns_fakeip", "address": "fakeip" }
			],
			"rules": [
			  { "outbound": "any", "server": "localdns", "disable_cache": true },
			  { "clash_mode": "Global", "server": "proxydns" },
			  { "clash_mode": "Direct", "server": "localdns" },
			  { "rule_set": "geosite-cn", "server": "localdns" },
			  { "rule_set": "geosite-geolocation-!cn", "server": "proxydns" },
			  { "rule_set": "geosite-geolocation-!cn", "query_type": ["A", "AAAA"], "server": "dns_fakeip" }
			],
			"fakeip": { "enabled": true, "inet4_range": "198.18.0.0/15", "inet6_range": "fc00::/18" },
			"independent_cache": true,
			"final": "proxydns"
		},
		"route": {
			"auto_detect_interface": true,
			"final": "select",
			"rules": [
				{ "inbound": "tun-in", "action": "sniff" },
				{ "protocol": "dns", "action": "hijack-dns" },
				{ "port": 443, "network": "udp", "action": "reject" },
				{ "clash_mode": "Direct", "outbound": "direct" },
				{ "clash_mode": "Global", "outbound": "select" },
				{ "rule_set": "geoip-cn", "outbound": "direct" },
				{ "rule_set": "geosite-cn", "outbound": "direct" },
				{ "ip_is_private": true, "outbound": "direct" },
				{ "rule_set": "geosite-geolocation-!cn", "outbound": "select" }
			]
		}
	};
	return JSON.stringify(sbConfig, null, 2);
}

/**
 * Generates the main HTML page.
 * @param {string} userID
 * @param {string | null} hostName
 * @returns {string}
 */
function getvlessConfig(userID, hostName) {
  const wvlessws = `vless://${userID}@${CDNIP}:8880?encryption=none&security=none&type=ws&host=${hostName}&path=%2F%3Fed%3D2560#${hostName}`;
  const pvlesswstls = `vless://${userID}@${CDNIP}:8443?encryption=none&security=tls&type=ws&host=${hostName}&sni=${hostName}&fp=random&path=%2F%3Fed%3D2560#${hostName}`;
  const note = `甬哥博客地址：https://ygkkk.blogspot.com\n甬哥YouTube频道：https://www.youtube.com/@ygkkk\n甬哥TG电报群组：https://t.me/ygkkktg\n甬哥TG电报频道：https://t.me/ygkkktgpd\n\nProxyIP使用nat64自动生成，无需设置`;
  const ty = `https://${hostName}/${userID}/ty`
  const cl = `https://${hostName}/${userID}/cl`
  const sb = `https://${hostName}/${userID}/sb`
  const pty = `https://${hostName}/${userID}/pty`
  const pcl = `https://${hostName}/${userID}/pcl`
  const psb = `https://${hostName}/${userID}/psb`
  const allnodes = `https://${hostName}/${userID}/allnodes`
  
  const allServersForShare = [...all_non_tls_servers.map(s => ({...s, tls: false})), ...all_tls_servers.map(s => ({...s, tls: true}))];
  const wkvlessshare = gettyConfig(userID, hostName, allServersForShare);

  const pgvlessshare = gettyConfig(userID, hostName, all_tls_servers.map(s => ({...s, tls: true})));	

  const noteshow = note.replace(/\n/g, '<br>');
  const displayHtml = `
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
<style>
.limited-width { max-width: 200px; overflow: auto; word-wrap: break-word; }
</style>
</head>
<script>
function copyToClipboard(text) {
  const input = document.createElement('textarea');
  input.style.position = 'fixed';
  input.style.opacity = 0;
  input.value = text;
  document.body.appendChild(input);
  input.select();
  document.execCommand('Copy');
  document.body.removeChild(input);
  alert('已复制到剪贴板');
}
</script>
`;
if (hostName.includes("workers.dev")) {
return `
<br><br>${displayHtml}
<body>
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>Cloudflare-workers/pages-vless代理脚本(已重构)</h1>
	    <hr><p>${noteshow}</p><hr><hr><hr><br><br>
            <h3>1：CF-workers-vless+ws节点</h3>
			<table class="table">
				<thead><tr><th>节点特色：</th><th>单节点链接如下：</th></tr></thead>
				<tbody><tr><td class="limited-width">关闭了TLS加密，无视域名阻断</td><td class="limited-width">${wvlessws}</td>
				<td><button class="btn btn-primary" onclick="copyToClipboard('${wvlessws}')">点击复制链接</button></td></tr></tbody>
			</table>
            <h5>客户端参数如下：</h5>
            <ul>
                <li>客户端地址(address)：${CDNIP}</li>
                <li>端口(port)：8880</li>
                <li>用户ID(uuid)：${userID}</li>
                <li>传输协议(network)：ws 或者 websocket</li>
                <li>伪装域名(host)：${hostName}</li>
                <li>路径(path)：/?ed=2560</li>
		        <li>传输安全(TLS)：关闭</li>
            </ul>
            <hr><hr><hr><br><br>
            <h3>2：CF-workers-vless+ws+tls节点</h3>
			<table class="table">
				<thead><tr><th>节点特色：</th><th>单节点链接如下：</th></tr></thead>
				<tbody><tr><td class="limited-width">启用了TLS加密，<br>如果客户端支持分片(Fragment)功能，建议开启，防止域名阻断</td><td class="limited-width">${pvlesswstls}</td>	
				<td><button class="btn btn-primary" onclick="copyToClipboard('${pvlesswstls}')">点击复制链接</button></td></tr></tbody>
			</table>
            <h5>客户端参数如下：</h5>
            <ul>
                <li>客户端地址(address)：${CDNIP}</li>
                <li>端口(port)：8443</li>
                <li>用户ID(uuid)：${userID}</li>
                <li>传输协议(network)：ws 或者 websocket</li>
                <li>伪装域名(host)：${hostName}</li>
                <li>路径(path)：/?ed=2560</li>
                <li>传输安全(TLS)：开启</li>
                <li>跳过证书验证(allowlnsecure)：false</li>
			</ul>
			<hr><hr><hr><br><br>
			<h3>3：聚合通用、Clash-meta、Sing-box订阅链接如下：</h3>
			<hr><p>注意：<br>1、默认每个订阅链接包含所有TLS+非TLS节点<br>2、当前workers域名作为订阅链接，需通过代理进行订阅更新<br>3、如使用的客户端不支持分片功能，则TLS节点不可用</p><hr>
			<table class="table">
				<thead><tr><th>聚合通用分享链接 (可直接导入客户端)：</th></tr></thead>
				<tbody><tr><td><button class="btn btn-primary" onclick="copyToClipboard('${wkvlessshare}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>聚合通用订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${ty}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${ty}')">点击复制链接</button></td></tr></tbody>
			</table>	
			<table class="table">
				<thead><tr><th>Clash-meta订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${cl}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${cl}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>Sing-box订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${sb}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${sb}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>所有节点纯文本链接 (方便逐个复制)：</th></tr></thead>
				<tbody><tr><td class="limited-width"><a href="${allnodes}" target="_blank">${allnodes}</a></td><td><button class="btn btn-primary" onclick="window.open('${allnodes}', '_blank')">点击打开</button></td></tr></tbody>
			</table><br><br>
        </div></div></div></body>`;
  } else {
    return `
<br><br>${displayHtml}
<body>
<div class="container">
    <div class="row">
        <div class="col-md-12">
            <h1>Cloudflare-workers/pages-vless代理脚本(已重构)</h1>
			<hr><p>${noteshow}</p><hr><hr><hr><br><br>
            <h3>1：CF-pages/workers/自定义域-vless+ws+tls节点</h3>
			<table class="table">
				<thead><tr><th>节点特色：</th><th>单节点链接如下：</th></tr></thead>
				<tbody><tr><td class="limited-width">启用了TLS加密，<br>如果客户端支持分片(Fragment)功能，可开启，防止域名阻断</td><td class="limited-width">${pvlesswstls}</td>
				<td><button class="btn btn-primary" onclick="copyToClipboard('${pvlesswstls}')">点击复制链接</button></td></tr></tbody>
			</table>
            <h5>客户端参数如下：</h5>
            <ul>
                <li>客户端地址(address)：${CDNIP}</li>
                <li>端口(port)：8443</li>
                <li>用户ID(uuid)：${userID}</li>
                <li>传输协议(network)：ws 或者 websocket</li>
                <li>伪装域名(host)：${hostName}</li>
                <li>路径(path)：/?ed=2560</li>
                <li>传输安全(TLS)：开启</li>
                <li>跳过证书验证(allowlnsecure)：false</li>
			</ul><hr><hr><hr><br><br>
			<h3>2：聚合通用、Clash-meta、Sing-box订阅链接如下：</h3>
			<hr><p>注意：以下订阅链接仅包含TLS节点</p><hr>
			<table class="table">
				<thead><tr><th>聚合通用分享链接 (可直接导入客户端)：</th></tr></thead>
				<tbody><tr><td><button class="btn btn-primary" onclick="copyToClipboard('${pgvlessshare}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>聚合通用订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${pty}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${pty}')">点击复制链接</button></td></tr></tbody>
			</table>	
			<table class="table">
				<thead><tr><th>Clash-meta订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${pcl}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${pcl}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>Sing-box订阅链接：</th></tr></thead>
				<tbody><tr><td class="limited-width">${psb}</td><td><button class="btn btn-primary" onclick="copyToClipboard('${psb}')">点击复制链接</button></td></tr></tbody>
			</table>
			<table class="table">
				<thead><tr><th>所有节点纯文本链接 (方便逐个复制)：</th></tr></thead>
				<tbody><tr><td class="limited-width"><a href="${allnodes}" target="_blank">${allnodes}</a></td><td><button class="btn btn-primary" onclick="window.open('${allnodes}', '_blank')">点击打开</button></td></tr></tbody>
			</table><br><br>
        </div></div></div></body>`;
  }
}
// ================= DYNAMIC CONFIG FUNCTIONS END =================