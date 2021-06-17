lambdas-pre-deploy:
	tee  Lambdas/dispatch_fp_diners/src/.conf Lambdas/dispatch_ue_diners/src/.conf Lambdas/get_fp_detail/src/.conf Lambdas/get_fp_list/src/.conf Lambdas/get_ue_detail/src/.conf Lambdas/get_ue_list/src/.conf Lambdas/log_stepfunction_result/src/.conf < .conf >/dev/null

	tee Lambdas/dispatch_fp_diners/src/conf.py Lambdas/dispatch_ue_diners/src/conf.py Lambdas/get_fp_detail/src/conf.py Lambdas/get_fp_list/src/conf.py Lambdas/get_ue_detail/src/conf.py Lambdas/get_ue_list/src/conf.py Lambdas/log_stepfunction_result/src/conf.py < conf.py >/dev/null

	tee Lambdas/dispatch_fp_diners/src/.env Lambdas/dispatch_ue_diners/src/.env Lambdas/get_fp_detail/src/.env Lambdas/get_fp_list/src/.env Lambdas/get_ue_detail/src/.env Lambdas/get_ue_list/src/.env Lambdas/log_stepfunction_result/src/.env < .env >/dev/null

	tee Lambdas/dispatch_fp_diners/src/env.py Lambdas/dispatch_ue_diners/src/env.py Lambdas/get_fp_detail/src/env.py Lambdas/get_fp_list/src/env.py Lambdas/get_ue_detail/src/env.py Lambdas/get_ue_list/src/env.py Lambdas/log_stepfunction_result/src/env.py < env.py >/dev/null

	tee Lambdas/dispatch_fp_diners/src/utils.py Lambdas/dispatch_ue_diners/src/utils.py Lambdas/get_fp_detail/src/utils.py Lambdas/get_fp_list/src/utils.py Lambdas/get_ue_detail/src/utils.py Lambdas/get_ue_list/src/utils.py Lambdas/log_stepfunction_result/src/utils.py < utils.py >/dev/null

	tee Lambdas/get_ue_detail/src/crawl_ue.py Lambdas/get_ue_list/src/crawl_ue.py  < Crawlers/crawl_ue.py >/dev/null

	tee Lambdas/get_fp_detail/src/crawl_fp.py Lambdas/get_fp_list/src/crawl_fp.py  < Crawlers/crawl_fp.py >/dev/null

	tee Lambdas/get_ue_detail/src/api_ue.json < Crawlers/api_ue.json >/dev/null

	tee Lambdas/get_fp_detail/src/api_fp.json Lambdas/get_fp_list/src/api_fp.json < Crawlers/api_fp.json >/dev/null

	tee Lambdas/dispatch_ue_targets/targets_ue.json < Crawlers/targets_ue.json >/dev/null

	tee Lambdas/get_fp_list/src/target_fp.json < Crawlers/target_fp.json >/dev/null

