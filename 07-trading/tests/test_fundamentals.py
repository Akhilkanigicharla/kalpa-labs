import pytest

from src.fundamentals import Company, cagr, score

# The FinEdge worksheet's own example company ("Alpha Consumer Limited", FY21-FY24).
ALPHA = dict(
    name="Alpha Consumer (FinEdge example)",
    revenue=[10842, 12443, 14965, 17428],
    net_profit=[1746, 2058, 2614, 3115],
    operating_margin=[0.174, 0.179, 0.185, 0.188],
    roe=[0.196, 0.201, 0.212, 0.215],
    roce=[0.248, 0.256, 0.267, 0.271],
    debt_equity=0.06,
    free_cash_flow=[1482, 1776, 2221, 2686],
    promoter_holding=[0.624, 0.624, 0.624, 0.624],
    pe=40.2, peer_pe=38.5,
)


def by_name(rep):
    return {c.name: c for c in rep.checks}


def test_cagr_matches_worksheet():
    # worksheet prints 17.2% revenue CAGR, but its own numbers give 17.1%
    # ((17428/10842)^(1/3) - 1 = 17.13%): the infographic rounded wrong. Net profit 21.3% matches.
    assert round(cagr(ALPHA["revenue"]) * 100, 1) == 17.1
    assert round(cagr(ALPHA["net_profit"]) * 100, 1) == 21.3


def test_finedge_example_scores_well():
    rep = score(Company(**ALPHA))
    c = by_name(rep)
    assert c["Revenue growth"].status == "pass"
    assert c["Profitability"].status == "pass"
    assert c["Debt"].status == "pass"
    assert c["Cash-flow quality"].status == "pass"          # 8150/9533 = 85%
    assert c["Promoter holding"].status == "pass"
    assert c["ROE / ROCE"].status == "watch"                 # FY21 ROE 19.6% < 20%
    assert c["Valuation vs peers"].status == "watch"         # 40.2/38.5 = 1.04x, "not cheap"
    assert c["Margin of safety"].status == "skip"
    assert rep.red_flags == []
    assert 80 <= rep.score <= 95
    assert "not investment advice" in rep.table()


def test_red_flags_and_fails():
    bad = dict(ALPHA, name="Bad Co", revenue=[100, 90, 95, 110], net_profit=[10, -5, 8, 20],
               free_cash_flow=[9, 2, 1, -3], debt_equity=1.8, promoter_holding=[0.6, 0.5],
               promoter_pledged=0.35, price=120, fair_value=100)
    rep = score(Company(**bad))
    c = by_name(rep)
    assert c["Debt"].status == "fail"
    assert c["Profitability"].status == "fail"
    assert c["Promoter holding"].status == "fail"
    assert c["Margin of safety"].status == "fail"
    assert "ABOVE" in c["Margin of safety"].why
    assert set(rep.red_flags) == {"Revenue fell in at least one year", "Profit rising while free cash flow falls",
                                  "Promoter shares are pledged"}
    assert rep.score < 40


def test_bad_input_is_rejected():
    with pytest.raises(ValueError):
        score(Company(**dict(ALPHA, roe=[0.2])))
    with pytest.raises(ValueError):
        cagr([0, 10])
