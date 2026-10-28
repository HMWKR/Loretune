'use strict';
// Audit process only: fail on any accidental real network/listener attempt.
const deny=()=>{throw Error('AUDIT_OFFLINE_NETWORK_FORBIDDEN');};
require('node:net').Socket.prototype.connect=deny;
require('node:net').Server.prototype.listen=deny;
for(const name of ['node:http','node:https']){const m=require(name);m.request=deny;m.get=deny;}
require('node:tls').connect=deny;
globalThis.fetch=deny;
