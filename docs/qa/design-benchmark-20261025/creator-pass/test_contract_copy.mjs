import assert from 'node:assert/strict';
import {timelineProposalCopy,memoryProposalCopy,renderReceiptCopy} from './contract-copy.mjs';
const checks=[];function test(name,fn){fn();checks.push(name)}
test('proposed edit does not imply applied',()=>assert.match(timelineProposalCopy({status:'proposed',applied:false}).status,/아직 적용하지/));
test('applied edit still needs output approval',()=>assert.match(timelineProposalCopy({applied:true,output_approved:false}).note,/새 편집 버전을 승인/));
test('memory proposal does not imply canonical save',()=>assert.match(memoryProposalCopy({status:'proposed',canonical_approved:false}).status,/아직 반영하지/));
test('accepted queued is not output complete',()=>assert.equal(renderReceiptCopy({status:'accepted',state:'queued',finished_verified:false,output_approved:false}).status,'출력 대기'));
test('existing receipt asks for existing job status',()=>assert.match(renderReceiptCopy({status:'existing',state:'running'}).note,/기존 작업/));
test('verified file remains separate from delivery approval',()=>assert.equal(renderReceiptCopy({finished_verified:true,output_approved:false}).status,'출력 파일 준비됨 · 납품 검토 전'));
test('delivery approval requires verified file flag',()=>assert.notEqual(renderReceiptCopy({output_approved:true,finished_verified:false}).status,'납품 검토 승인됨'));
test('internal fields do not leak through presentation adapter',()=>{const raw={job_id:'private-job',proposal_id:'private-proposal',grant_id:'private-grant'};for(const fn of [timelineProposalCopy,memoryProposalCopy,renderReceiptCopy])assert.ok(!JSON.stringify(fn(raw)).includes('private-'));});
console.log(JSON.stringify({passed:checks.length,checks},null,2));
