# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSafeBox(TransactionCase):
    def setUp(self):
        super(TestSafeBox, self).setUp()
        self.partner = self.env["res.partner"].create(
            {"name": "Partner", "company_id": False}
        )
        self.user = self.env["res.users"].create(
            {
                "name": "User",
                "login": "user_safe_box",
                "groups_id": [(4, self.ref("safe_box.group_safe_box_user"))],
            }
        )
        self.chart_template_id = self.env["account.chart.template"].search(
            [("visible", "=", True)], limit=1
        )
        self.safe_box_group = self.env["safe.box.group"].create(
            {
                "name": "Group",
                "code": "SB",
                "currency_id": self.ref("base.USD"),
            }
        )
        self.coin = self.env["safe.box.coin"].create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "name": "Coin",
                "rate": 1,
            }
        )
        self.safe_box_01 = self.env["safe.box"].create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "name": "SB 01",
                "coin_ids": [(4, self.coin.id)],
                "user_ids": [(4, self.user.id)],
            }
        )
        self.safe_box_02 = self.env["safe.box"].create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "name": "SB 02",
                "coin_ids": [(4, self.coin.id)],
            }
        )
        self.company_01 = self.create_company("Company 1")
        self.company_02 = self.create_company("Company 2")
        self.account_01 = self.env["account.account"].create(
            {
                "name": "Account 01",
                "code": "001",
                "company_id": self.company_01.id,
                "user_type_id": self.ref(
                    "account.data_account_type_liquidity"
                ),
                "safe_box_group_id": self.safe_box_group.id,
            }
        )
        self.account_02 = self.env["account.account"].create(
            {
                "name": "Account 02",
                "code": "002",
                "company_id": self.company_02.id,
                "user_type_id": self.ref(
                    "account.data_account_type_liquidity"
                ),
                "safe_box_group_id": self.safe_box_group.id,
            }
        )
        self.journal_01 = self.env["account.journal"].create(
            {
                "name": "Journal",
                "code": "J01",
                "company_id": self.company_01.id,
                "type": "cash",
            }
        )
        self.journal_02 = self.env["account.journal"].create(
            {
                "name": "Journal",
                "code": "J02",
                "company_id": self.company_02.id,
                "type": "cash",
            }
        )
        self.account_03 = self.env["account.account"].create(
            {
                "name": "Account 03",
                "code": "003",
                "company_id": self.company_01.id,
                "user_type_id": self.ref(
                    "account.data_account_type_liquidity"
                ),
            }
        )
        self.account_04 = self.env["account.account"].create(
            {
                "name": "Account 04",
                "code": "004",
                "company_id": self.company_02.id,
                "user_type_id": self.ref(
                    "account.data_account_type_liquidity"
                ),
            }
        )

    def create_company(self, name):
        return self.env["res.company"].create(
            {"name": name, "vat": 1, "currency_id": self.ref("base.USD")}
        )

    def test_safe_box(self):
        self.assertTrue(self.safe_box_group.account_ids)
        with self.assertRaises(ValidationError):
            self.env["wizard.safe.box.move"].create(
                {
                    "safe_box_group_id": self.safe_box_group.id,
                    "initial_safe_box_id": self.safe_box_01.id,
                    "end_safe_box_id": self.safe_box_02.id,
                    "amount": 100,
                }
            ).run()
        self.env["wizard.safe.box.move.external"].create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "safe_box_id": self.safe_box_01.id,
                "journal_id": self.journal_02.id,
                "account_id": self.account_04.id,
                "partner_id": self.partner.id,
                "amount": 100,
            }
        ).run()
        self.safe_box_group.recompute_amount()
        self.assertEqual(self.safe_box_01.amount, 100)
        self.assertEqual(self.safe_box_02.amount, 0)
        with self.assertRaises(ValidationError):
            self.env["wizard.safe.box.move"].sudo(user=self.user.id).create(
                {
                    "safe_box_group_id": self.safe_box_group.id,
                    "initial_safe_box_id": self.safe_box_01.id,
                    "end_safe_box_id": self.safe_box_02.id,
                    "amount": 50,
                }
            ).run()
        self.safe_box_02.write({"user_ids": [(4, self.user.id)]})
        self.env["wizard.safe.box.move"].sudo(user=self.user.id).create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "initial_safe_box_id": self.safe_box_01.id,
                "end_safe_box_id": self.safe_box_02.id,
                "amount": 50,
            }
        ).run()
        self.env["wizard.safe.box.move"].create(
            {
                "safe_box_group_id": self.safe_box_group.id,
                "initial_safe_box_id": self.safe_box_01.id,
                "end_safe_box_id": self.safe_box_02.id,
                "amount": 50,
            }
        ).run()
        self.safe_box_group.recompute_amount()
        count = (
            self.env["wizard.safe.box.count"]
            .with_context(default_safe_box_group_id=self.safe_box_group.id)
            .new({})
        )
        count.safe_box_id = self.safe_box_02
        count._onchange_safe_box_id()
        count.validate()
        self.assertEqual(count.state, "different")
        self.assertTrue(count.coin_ids)
        count.coin_ids[0].value = 100
        count.validate()
        self.assertEqual(count.state, "equal")
        self.assertTrue(count.coin_ids)
        self.assertEqual(self.safe_box_01.amount, 0)
        self.assertEqual(self.safe_box_02.amount, 100)
        with self.assertRaises(ValidationError):
            self.account_02.write({"safe_box_group_id": False})
        with self.assertRaises(ValidationError):
            self.account_04.write(
                {"safe_box_group_id": self.safe_box_group.id}
            )
        with self.assertRaises(ValidationError):
            self.env["wizard.safe.box.move.external"].create(
                {
                    "safe_box_group_id": self.safe_box_group.id,
                    "safe_box_id": self.safe_box_01.id,
                    "journal_id": self.journal_02.id,
                    "account_id": self.account_04.id,
                    "amount": -100,
                }
            ).run()
