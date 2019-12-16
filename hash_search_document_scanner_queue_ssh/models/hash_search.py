# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
from odoo import api, models
from odoo.addons.queue_job.job import job
from odoo.modules.registry import Registry
import stat
import time
import logging

_logger = logging.getLogger(__name__)
try:
    from paramiko.client import SSHClient
except (ImportError, IOError) as err:
    _logger.info(err)


class HashSearch(models.Model):
    _inherit = "hash.search"

    @api.model
    def cron_ssh_move_documents(
        self,
        host=False,
        port=False,
        user=False,
        password=False,
        ssh_path=False,
    ):
        dest_path = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hash_search_document_scanner.path", default=False)
        )
        connection = SSHClient()
        connection.load_system_host_keys()

        if not dest_path:
            return False
        if not host:
            host = self.env["ir.config_parameter"].get_param(
                "hash_search_document_scanner_queue_ssh.host", default=False
            )
        if not port:
            port = int(
                self.env["ir.config_parameter"].get_param(
                    "hash_search_document_scanner_queue_ssh.port", default="0"
                )
            )
        if not user:
            user = self.env["ir.config_parameter"].get_param(
                "hash_search_document_scanner_queue_ssh.user", default=False
            )
        if not password:
            password = self.env["ir.config_parameter"].get_param(
                "hash_search_document_scanner_queue_ssh.password",
                default=False,
            )

        if not ssh_path:
            ssh_path = self.env["ir.config_parameter"].get_param(
                "hash_search_document_scanner_queue_ssh.ssh_path",
                default=False,
            )
        connection.connect(
            hostname=host, port=port, username=user, password=password
        )
        sftp = connection.open_sftp()
        if ssh_path:
            sftp.chdir(ssh_path)
        elements = sftp.listdir_attr(".")
        min_time = int(time.time()) - 60
        single_commit = self.env.context.get("scanner_single_commit", False)
        for element in elements:
            if element.st_atime > min_time and not self.env.context.get(
                "scanner_ignore_time", False
            ):
                continue
            if stat.S_ISDIR(element.st_mode):
                continue
            filename = element.filename
            new_element = os.path.join(dest_path, filename)
            if not single_commit:
                new_cr = Registry(self.env.cr.dbname).cursor()
            try:
                sftp.get(filename, new_element)
                if single_commit:
                    obj = self.env[self._name].browse()
                else:
                    obj = (
                        api.Environment(
                            new_cr, self.env.uid, self.env.context
                        )[self._name]
                        .browse()
                        .with_delay()
                    )
                obj.process_document(new_element)
                if not single_commit:
                    new_cr.commit()
            except Exception:
                if os.path.exists(new_element):
                    os.unlink(new_element)
                if not single_commit:
                    new_cr.rollback()  # error, rollback everything atomically
                raise
            finally:
                if not single_commit:
                    new_cr.close()
            sftp.remove(element.filename)
        sftp.close()
        connection.close()
        return True

    @api.model
    @job(default_channel="root.scanner")
    def process_document(self, element):
        return super().process_document(element)
