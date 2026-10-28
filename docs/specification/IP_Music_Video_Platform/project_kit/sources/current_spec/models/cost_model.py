"""Offline cost scenarios, not measured product costs or a commercial quotation."""
import argparse
import hashlib
import json
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path


def calculate(config, seconds=60, mode='hybrid', model='gen4_turbo', candidates=2,
              monthly_outputs=4, first_project=False, support_minutes=None):
    def dec(value):
        result = Decimal(str(value))
        if not result.is_finite():
            raise ValueError('All numeric inputs must be finite.')
        return result

    duration = dec(seconds)
    count = dec(monthly_outputs)
    candidate_count = dec(candidates)
    if duration <= 0 or count <= 0 or count != count.to_integral_value():
        raise ValueError('Duration must be positive and monthly_outputs a positive integer.')
    if candidate_count < 1 or candidate_count != candidate_count.to_integral_value():
        raise ValueError('Candidates must be a positive integer, including the first candidate.')
    if candidate_count > config['max_candidates_without_new_approval']:
        raise ValueError('More than three candidates requires a new quote and approval; not this scenario.')
    if mode not in config['modes'] or model not in config['video_models']:
        raise ValueError('Unknown mode or model.')
    for key in ['fx_krw_per_usd', 'monthly_team_subscription_krw', 'usage_markup_multiplier',
                'keyframe_usd_per_image', 'platform_support_hourly_krw']:
        if dec(config[key]) < 0:
            raise ValueError('Negative model parameter: ' + key)
    share = dec(config['modes'][mode]['generated_video_share'])
    clip = dec(config['planned_clip_seconds'])
    if not Decimal('0') <= share <= Decimal('1') or clip <= 0:
        raise ValueError('Invalid generated share or clip duration.')
    generated_seconds = duration * share
    shots = (generated_seconds / clip).to_integral_value(rounding=ROUND_CEILING)
    billed_seconds = shots * clip * candidate_count
    keyframes = shots * dec(config['keyframe_candidates_per_generated_shot'])
    video_usd = billed_seconds * dec(config['video_models'][model]['usd_per_billed_second'])
    image_usd = keyframes * dec(config['keyframe_usd_per_image'])
    minutes = duration / Decimal('60')
    allowances = config['non_generation_allowances_usd']
    analysis_usd = dec(allowances['analysis_fixed']) + minutes * dec(allowances['analysis_per_output_minute'])
    render_usd = minutes * dec(allowances['render_per_output_minute'])
    storage_usd = minutes * dec(allowances['storage_egress_per_output_minute'])
    other_usd = analysis_usd + render_usd + storage_usd
    variable_usd = video_usd + image_usd + other_usd
    variable_krw = variable_usd * dec(config['fx_krw_per_usd'])
    allocated_subscription = dec(config['monthly_team_subscription_krw']) / count
    usage_charge = variable_krw * dec(config['usage_markup_multiplier'])
    customer_cash = allocated_subscription + usage_charge
    support = dec(support_minutes) if support_minutes is not None else (
        dec(config['platform_support_minutes_fixed']) + minutes * dec(config['platform_support_minutes_per_output_minute']))
    if support < 0:
        raise ValueError('support_minutes must not be negative.')
    support_cost = support / Decimal('60') * dec(config['platform_support_hourly_krw'])
    fixed_cost = dec(config['platform_fixed_cost_per_team_month_krw']) / count
    payment_fee = customer_cash * dec(config['payment_fee_rate_assumption'])
    refund_reserve = customer_cash * dec(config['refund_reserve_rate_assumption'])
    contribution = customer_cash - variable_krw - support_cost - fixed_cost - payment_fee - refund_reserve
    customer_minutes = minutes * dec(config['customer_active_minutes_per_output_minute'])
    if first_project:
        customer_minutes += dec(config['first_project_onboarding_minutes_assumption'])
    customer_time_cost = customer_minutes / Decimal('60') * dec(config['customer_hourly_krw_assumption'])

    def money(value):
        return float(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return {
        'scenario_id': f'COST-{int(duration):03d}-{mode.upper()}',
        'scenario_id_scope': 'Duration and mode family; use calculation_id for an exact input combination.',
        'calculation_id': 'CALC-' + hashlib.sha256(json.dumps({
            'config': config, 'seconds': str(duration), 'mode': mode, 'model': model,
            'candidates': str(candidate_count), 'monthly_outputs': str(count),
            'first_project': bool(first_project), 'support_minutes': str(support)
        }, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:20],
        'model_version': config['version'],
        'evidence_state': 'modeled_not_measured',
        'duration_seconds': float(duration),
        'mode': mode, 'model': model, 'monthly_outputs': int(count),
        'candidates_per_generated_shot': int(candidate_count),
        'first_project': bool(first_project),
        'generated_accepted_seconds': float(generated_seconds),
        'generated_shot_count': int(shots),
        'billed_video_seconds': float(billed_seconds),
        'keyframe_image_count': int(keyframes),
        'video_generation_usd': money(video_usd),
        'keyframe_generation_usd': money(image_usd),
        'analysis_allowance_usd': money(analysis_usd),
        'render_allowance_usd': money(render_usd),
        'storage_egress_allowance_usd': money(storage_usd),
        'other_variable_allowance_usd': money(other_usd),
        'variable_external_cost_usd': money(variable_usd),
        'fx_krw_per_usd_budget': float(dec(config['fx_krw_per_usd'])),
        'variable_external_cost_krw': money(variable_krw),
        'allocated_subscription_krw': money(allocated_subscription),
        'usage_charge_hypothesis_krw': money(usage_charge),
        'customer_cash_excluding_tax_krw': money(customer_cash),
        'platform_support_minutes_assumption': float(support),
        'platform_support_cost_krw': money(support_cost),
        'platform_fixed_cost_allocation_krw': money(fixed_cost),
        'payment_fee_allowance_krw': money(payment_fee),
        'refund_reserve_allowance_krw': money(refund_reserve),
        'contribution_before_dev_sales_overheads_krw': money(contribution),
        'contribution_margin_pct': money(contribution / customer_cash * 100) if customer_cash else None,
        'customer_active_minutes_assumption': float(customer_minutes),
        'customer_labor_cost_assumption_krw': money(customer_time_cost),
        'customer_economic_cost_excluding_tax_krw': money(customer_cash + customer_time_cost),
        'excluded': config['output_scope']['excluded'],
        'quality_equivalence_verified': False,
        'product_support_verified': False,
        'native_1080p_claim': False,
        'price_source_ids': ['S-C01'],
        'note': 'Budget scenario only; not a measured average, price offer, success guarantee, or outsourced-service equivalence.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('cost_model.json'))
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--mode', choices=['asset', 'hybrid', 'gen'], default='hybrid')
    parser.add_argument('--model', choices=['gen4_turbo', 'gen4.5'], default='gen4_turbo')
    parser.add_argument('--candidates', type=int, default=2)
    parser.add_argument('--monthly-outputs', type=int, default=4)
    parser.add_argument('--first-project', action='store_true')
    parser.add_argument('--support-minutes', type=float)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding='utf-8'))
        result = calculate(config, args.seconds, args.mode, args.model, args.candidates,
                           args.monthly_outputs, args.first_project, args.support_minutes)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + '\n', encoding='utf-8')
    else:
        print(text)


if __name__ == '__main__':
    main()
