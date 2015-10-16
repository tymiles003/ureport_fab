# ureport_fab
One step deploy for ureport on Ubuntu server

## To deploy to production or test environment

* Edit the config files in `resources` directory(If you want to make changes to those, especially `settings` directory)
* Run `fab deploy` to deploy to test
* Run `fab deploy:True` to deploy to production
* Run `fab deply:to_pod=True,user=xkamto,prep_server=True,syncdb=True` to run a fres install on production

## Defaults

* `user=www-data`- This is the default user running the webapplication
* `source=https://github.com/rapidpro/ureport.git`- The repo where to fetch ureport code(Must be git)
* `root_dir=/var/www/ureport/`- The root directory for the application
* `workon_path=/var/www/.virtualenvs`- The root directory for the virtualenvs
* `prep_server=False`- Whether to prepare server first(Done on new server, installing all distribution requirements) This flag will automatically set `sync_db=True`
* `syncdb=False`- Whether to sync db and run new migration, if any
