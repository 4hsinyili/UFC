copy-env-conf-to-lambdas:
	tee  Lambdas/dispatch_fp_diners/src/.conf Lambdas/dispatch_ue_diners/src/.conf Lambdas/get_fp_detail/src/.conf Lambdas/get_fp_list/src/.conf Lambdas/get_ue_detail/src/.conf Lambdas/get_ue_list/src/.conf Lambdas/log_stepfunction_result/src/.conf < .conf >/dev/null

	tee Lambdas/dispatch_fp_diners/src/conf.py Lambdas/dispatch_ue_diners/src/conf.py Lambdas/get_fp_detail/src/conf.py Lambdas/get_fp_list/src/conf.py Lambdas/get_ue_detail/src/conf.py Lambdas/get_ue_list/src/conf.py Lambdas/log_stepfunction_result/src/conf.py < conf.py >/dev/null

	tee Lambdas/dispatch_fp_diners/src/.env Lambdas/dispatch_ue_diners/src/.env Lambdas/get_fp_detail/src/.env Lambdas/get_fp_list/src/.env Lambdas/get_ue_detail/src/.env Lambdas/get_ue_list/src/.env Lambdas/log_stepfunction_result/src/.env < .env >/dev/null

	tee Lambdas/dispatch_fp_diners/src/env.py Lambdas/dispatch_ue_diners/src/env.py Lambdas/get_fp_detail/src/env.py Lambdas/get_fp_list/src/env.py Lambdas/get_ue_detail/src/env.py Lambdas/get_ue_list/src/env.py Lambdas/log_stepfunction_result/src/env.py < env.py >/dev/null

