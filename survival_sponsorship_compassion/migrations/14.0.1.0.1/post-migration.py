from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    wp = env["wordpress.configuration"].get_config()
    wp.write({"survival_sponsorship_url": "/parrainez-une-maman-et-son-bebe/#form"})
    wp.with_context(lang="de_DE").write(
        {"survival_sponsorship_url": "/de/mutter-und-babys-patenschaft/#form"}
    )
    wp.with_context(lang="it_IT").write(
        {"survival_sponsorship_url": "/it/sostieni-una-mamma-e-il-suo-bambino/#form"}
    )
