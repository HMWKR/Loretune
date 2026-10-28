"""Tool-definition bytes as sent on the Anthropic wire (strict, anthropic_wire_schema), per permission mode.

Usage (project root): python3.15 -B measure_tools.py <code-dir>
<code-dir> is searched before the project root, so start/ measures the pre-SRV-r2 code.
"""
import copy, json, sys
sys.path[:0] = [sys.argv[1], '.']
import agent_preferences, chat_general, chat_models, chat_protocols
def wire(names):
    tools = [copy.deepcopy(d) for d in chat_protocols.tool_definitions('anthropic') if d['name'] in names]
    for d in tools:d['strict'] = True;d['input_schema'] = chat_models.anthropic_wire_schema(d['input_schema'])
    return len(json.dumps(tools, ensure_ascii=False, allow_nan=False).encode('utf-8'))
full = list(chat_general.ALLOWED_TOOLS);read = [n for n in full if n in agent_preferences.READ_TOOLS]
reason = {d['name']:d['input_schema']['properties']['model_reason'] for d in chat_protocols.tool_definitions('anthropic') if 'model_reason' in d['input_schema']['properties']}
print(json.dumps(dict(code=sys.argv[1], review_full_access_tool_bytes=wire(full), read_only_tool_bytes=wire(read),
                      openai_all_tool_bytes=len(json.dumps(chat_protocols.tool_definitions('openai'), ensure_ascii=False).encode()),
                      model_reason_schema=reason), ensure_ascii=False, indent=1))
