"""T14 : le filtre masque chaque forme du §4.1."""

import unittest

import outils      # met le paquet dans le chemin d'import
from deployeur.filtre import filtrer


class TestFiltre(unittest.TestCase):
    def test_le_paquet_est_importable(self):
        self.assertTrue(outils.RACINE)

    def masque(self, texte, secret):
        sortie = filtrer(texte)
        self.assertNotIn(secret, sortie, texte)
        self.assertIn("***", sortie, texte)
        return sortie

    def test_affectations_dont_la_cle_contient_un_mot_sensible(self):
        cas = [
            ("TOKEN=abc123xyz", "abc123xyz"), ("GITHUB_TOKEN: ghp_abc", "ghp_abc"),
            ("client_secret = s3cr3t", "s3cr3t"), ("PASSWORD=hunter2", "hunter2"), ("db_passwd=hunter2", "hunter2"),
            ("PASS=hunter2", "hunter2"), ("API_KEY=k-12345", "k-12345"), ("SECRET_KEY=zzz111", "zzz111"),
            ("AUTH_USER=bob42", "bob42"), ("COOKIE=chocolat", "chocolat"), ("SESSION_ID=sess999", "sess999"),
            ("SENTRY_DSN=https://x@sentry/1", "x@sentry"), ("DATABASE_URL=postgres://u:pw@h/db", "pw@h"),
            ('{"api_key": "abcdef"}', "abcdef"), ("password='un mot de passe'", "un mot de passe"),
            ("Token=MiXeD", "MiXeD"),
        ]
        for texte, secret in cas:
            self.masque(texte, secret)

    def test_la_cle_reste_lisible(self):
        self.assertIn("API_KEY", filtrer("API_KEY=k-12345"))

    def test_mot_de_passe_d_une_url(self):
        s = self.masque("clone de https://alice:motdepasse@exemple.org/depot.git", "motdepasse")
        self.assertIn("https://alice:***@exemple.org/depot.git", s)
        self.masque("postgresql://app:p4ss@db:5432/x", "p4ss")

    def test_entetes_authorization_et_cookie(self):
        self.masque("Authorization: Bearer abc.def.ghi", "abc.def.ghi")
        self.masque("authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz")
        self.masque("Cookie: a=b; session_id=zzzz", "zzzz")
        self.masque("Set-Cookie: sid=trop-secret; Path=/", "trop-secret")

    def test_parametres_d_url(self):
        s = filtrer("GET /cb?code=abc123&state=zzz789&x=1 HTTP/1.1")
        self.assertNotIn("abc123", s)
        self.assertNotIn("zzz789", s)
        self.assertIn("x=1", s)
        self.masque("https://exemple.org/p?foo=1&token=tttt", "tttt")

    def test_webhook_discord(self):
        self.masque("POST https://discord.com/api/webhooks/123456/AbCdEf-gh_ij envoyé", "AbCdEf-gh_ij")
        self.masque("discordapp.com/api/webhooks/9/xyz", "xyz")

    def test_cles_sk_ant(self):
        self.masque("clé sk-ant-api03-AbCdEf012345", "AbCdEf012345")

    def test_blocs_de_32_caracteres_et_plus(self):
        hexa = "0123456789abcdef" * 2
        self.masque("empreinte " + hexa + " fin", hexa)
        b64 = "QWxhZGRpbjpvcGVuIHNlc2FtZQ==" + "AbCdEfGh"
        self.masque("jeton " + b64, b64)
        self.masque("sha " + "a" * 64, "a" * 64)
        # 31 caractères : conservé
        self.assertIn("a" * 31, filtrer("x " + "a" * 31 + " y"))

    def test_le_texte_ordinaire_est_conserve(self):
        t = "INFO: Application startup complete.\nUvicorn running on http://0.0.0.0:8000"
        self.assertEqual(filtrer(t), t)

    def test_vide(self):
        self.assertEqual(filtrer(""), "")
        self.assertEqual(filtrer(None), "")


if __name__ == "__main__":
    unittest.main()
