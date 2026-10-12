# English technical-workbench annotation review

Dataset: `english-technical-pdf-v2`

Dataset SHA-256: `a406fa9de8deec8bc5b3db2ad730b8b3255184f51af32ae3e3d7f4bb3cd942a4`

Quoted display omits trailing whitespace; canonical source bytes and labelled offsets remain unchanged.

All annotations are authored drafts. An independent reviewer must check the question, answerability, required facts, each complete alternative, source revision and offsets, category and grouping. Check surrounding source context, not just the excerpt. Record disagreements and resolve them before approval. Do not infer correctness from a successful loader check or approve unseen questions.

To approve reviewed labels, set each dataset query review.status to approved and review.reviewer to your identity. Keep the author identity. Add review notes for disputed or revised labels. Update the dataset version when facts/splits change; rerun recorded comparisons against the new manifest hash. No runner auto-approves annotations.

## pdf-venv-isolation

development / pdf-venv / paraphrase / draft

How do the tutorial virtual environments resolve applications requiring conflicting package versions?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-venv-isolation-1`:

Separate virtual environments let applications use different package versions; upgrading one application’s environment does not change the other’s packages.

Alternative `pdf-venv-isolation-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [819, 1189)

Labelled source text:

> Different applications can then use different virtual environments. To resolve the earlier example of conflicting re-
> quirements, application A can have its own virtual environment with version 1.0 installed while application B has
> anothervirtualenvironmentwithversion2.0. IfapplicationBrequiresalibrarybeupgradedtoversion3.0,thiswill
> notaffectapplicationA’senvironment.

Surrounding canonical source context:

> icationunabletorun.
> Thesolutionforthisproblemistocreatea virtual environment,aself-containeddirectorytreethatcontainsaPython
> installationforaparticularversionofPython,plusanumberofadditionalpackages.
> Different applications can then use different virtual environments. To resolve the earlier example of conflicting re-
> quirements, application A can have its own virtual environment with version 1.0 installed while application B has
> anothervirtualenvironmentwithversion2.0. IfapplicationBrequiresalibrarybeupgradedtoversion3.0,thiswill
> notaffectapplicationA’senvironment.
> 12.2 CreatingVirtualEnvironments
> Themoduleusedtocreateandmanagevirtualenvironmentsiscalled venv. venvwillusuallyinstallthemostrecent
> versionofPythonthatyouhaveavailable. IfyouhavemultipleversionsofPy

Review decision / disagreements / resolution: **pending**

## pdf-venv-module

development / pdf-venv / exact_api / draft

Which Python module creates virtual environments, and which Python installation does it usually use?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-venv-module-1`:

Use venv. The tutorial describes the usual Python as the most recent available one and says a specific version can be selected by invoking that interpreter.

Alternative `pdf-venv-module-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [1223, 1485)

Labelled source text:

> Themoduleusedtocreateandmanagevirtualenvironmentsiscalled venv. venvwillusuallyinstallthemostrecent
> versionofPythonthatyouhaveavailable. IfyouhavemultipleversionsofPythononyoursystem, youcanselecta
> specificPythonversionbyrunning python3orwhicheverversionyouwant.

Surrounding canonical source context:

> led while application B has
> anothervirtualenvironmentwithversion2.0. IfapplicationBrequiresalibrarybeupgradedtoversion3.0,thiswill
> notaffectapplicationA’senvironment.
> 12.2 CreatingVirtualEnvironments
> Themoduleusedtocreateandmanagevirtualenvironmentsiscalled venv. venvwillusuallyinstallthemostrecent
> versionofPythonthatyouhaveavailable. IfyouhavemultipleversionsofPythononyoursystem, youcanselecta
> specificPythonversionbyrunning python3orwhicheverversionyouwant.
> Tocreateavirtualenvironment,decideuponadirectorywhereyouwanttoplaceit,andrunthe venvmoduleasa
> scriptwiththedirectorypath:
> python3 -m venv tutorial -env
> This will create thetutorial-env directory if i

Review decision / disagreements / resolution: **pending**

## pdf-venv-activation

development / pdf-venv / paraphrase / draft

What does activating a virtual environment change about the shell and the python command?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-venv-activation-1`:

Activation changes the shell prompt to identify the environment and makes the python command use that environment’s Python installation.

Alternative `pdf-venv-activation-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [2456, 2668)

Labelled source text:

> Activating the virtual environment will change your shell’s prompt to show what virtual environment you’re using,
> andmodifytheenvironmentsothatrunning pythonwillgetyouthatparticularversionandinstallationofPython.

Surrounding canonical source context:

> n/activate
> 95
>
> PythonTutorial,Release3.11.0
> (This script is written for the bash shell. If you use thecsh or fish shells, there are alternateactivate.csh
> and activate.fishscriptsyoushoulduseinstead.)
> Activating the virtual environment will change your shell’s prompt to show what virtual environment you’re using,
> andmodifytheenvironmentsothatrunning pythonwillgetyouthatparticularversionandinstallationofPython.
> Forexample:
> $ source ~/envs/tutorial-env/bin/activate
> (tutorial-env) $ python
> Python 3.5.1 (default, May 6 2016, 10:59:36)
> ...
> >>> import sys
> >>> sys.path
> ['', '/usr/local/lib/python35.zip', ...,
> '~/

Review decision / disagreements / resolution: **pending**

## pdf-pip-version

development / pdf-venv / multi_span / draft

How does pip select an exact package version and upgrade it to the latest version in the tutorial?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.
- Included the exact-version installation command as concrete support for the expected installation syntax.

Fact `pdf-pip-version-1`:

Pin a package version using python -m pip install package==version (the example uses requests==2.6.0).

Alternative `pdf-pip-version-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [3656, 3828)

Labelled source text:

> You can also install a specific version of a package by giving the package name followed by== and the version
> number:
> (tutorial-env) $ python -m pip install requests==2.6.0

Surrounding canonical source context:

> v) $ python -m pip install novas
> Collecting novas
> Downloading novas-3.1.1.3.tar.gz (136kB)
> Installing collected packages: novas
> Running setup.py install for novas
> Successfully installed novas-3.1.1.3
> You can also install a specific version of a package by giving the package name followed by== and the version
> number:
> (tutorial-env) $ python -m pip install requests==2.6.0
> Collecting requests==2.6.0
> Using cached requests-2.6.0-py2.py3-none-any.whl
> Installing collected packages: requests
> Successfully installed requests-2.6.0
> Ifyoure-runthiscommand, pipwillnoticethatther

Fact `pdf-pip-version-2`:

Use python -m pip install --upgrade package to upgrade it to the latest version.

Alternative `pdf-pip-version-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [3983, 4210)

Labelled source text:

> Ifyoure-runthiscommand, pipwillnoticethattherequestedversionisalreadyinstalledanddonothing. Youcan
> supplyadifferentversionnumbertogetthatversion,oryoucanrun python -m pip install --upgrade
> toupgradethepackagetothelatestversion:

Surrounding canonical source context:

> -env) $ python -m pip install requests==2.6.0
> Collecting requests==2.6.0
> Using cached requests-2.6.0-py2.py3-none-any.whl
> Installing collected packages: requests
> Successfully installed requests-2.6.0
> Ifyoure-runthiscommand, pipwillnoticethattherequestedversionisalreadyinstalledanddonothing. Youcan
> supplyadifferentversionnumbertogetthatversion,oryoucanrun python -m pip install --upgrade
> toupgradethepackagetothelatestversion:
> (tutorial-env) $ python -m pip install --upgrade requests
> Collecting requests
> Installing collected packages: requests
> Found existing installation: requests 2.6.0
> Uninstalling requests-2.6.0:
> Successf

Review decision / disagreements / resolution: **pending**

## pdf-pip-freeze

development / pdf-venv / multi_span / draft

How does pip freeze format its package list, and how is that requirements file installed?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.
- Included the full install command and requirements filename, not only the abbreviated install -r prose.
- Added the package==version example to establish what requirements-compatible output looks like.

Fact `pdf-pip-freeze-1`:

pip freeze emits installed packages in requirements-compatible format, illustrated as package==version, and can write that list to requirements.txt.

Alternative `pdf-pip-freeze-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5249, 5589)

Labelled source text:

> python -m pip freeze will produce a similar list of the installed packages, but the output uses the format
> that python -m pip install expects. Acommonconventionistoputthislistina requirements.txt
> file:
> (tutorial-env) $ python -m pip freeze > requirements.txt
> (tutorial-env) $ cat requirements.txt
> novas==3.1.1.3
> numpy==1.9.2
> requests==2.7.0

Surrounding canonical source context:

> uires:
> python -m pip list willdisplayallofthepackagesinstalledinthevirtualenvironment:
> (tutorial-env) $ python -m pip list
> novas (3.1.1.3)
> numpy (1.9.2)
> pip (7.0.3)
> requests (2.7.0)
> setuptools (16.0)
> python -m pip freeze will produce a similar list of the installed packages, but the output uses the format
> that python -m pip install expects. Acommonconventionistoputthislistina requirements.txt
> file:
> (tutorial-env) $ python -m pip freeze > requirements.txt
> (tutorial-env) $ cat requirements.txt
> novas==3.1.1.3
> numpy==1.9.2
> requests==2.7.0
> The requirements.txtcanthenbecommittedtoversioncontrolandshippedaspartofanapplication. Users
> cantheninstallallthenecessarypackageswith install -r :
> (tutorial-env) $ python -m pip install -r requireme

Fact `pdf-pip-freeze-2`:

Install the packages listed in requirements.txt using python -m pip install -r requirements.txt.

Alternative `pdf-pip-freeze-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5590, 5796)

Labelled source text:

> The requirements.txtcanthenbecommittedtoversioncontrolandshippedaspartofanapplication. Users
> cantheninstallallthenecessarypackageswith install -r :
> (tutorial-env) $ python -m pip install -r requirements.txt

Surrounding canonical source context:

> . Acommonconventionistoputthislistina requirements.txt
> file:
> (tutorial-env) $ python -m pip freeze > requirements.txt
> (tutorial-env) $ cat requirements.txt
> novas==3.1.1.3
> numpy==1.9.2
> requests==2.7.0
> The requirements.txtcanthenbecommittedtoversioncontrolandshippedaspartofanapplication. Users
> cantheninstallallthenecessarypackageswith install -r :
> (tutorial-env) $ python -m pip install -r requirements.txt
> Collecting novas==3.1.1.3 (from -r requirements.txt (line 1))
> ...
> Collecting numpy==1.9.2 (from -r requirements.txt (line 2))
> ...
> Collecting requests==2.7.0 (from -r requirements.txt (line 3))
> ...
> In

Review decision / disagreements / resolution: **pending**

## pdf-pip-show-list

development / pdf-venv / exact_api / draft

Which pip commands show one package’s information and all installed packages?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-pip-show-list-1`:

python -m pip show displays information about one package.

Alternative `pdf-pip-show-list-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [4659, 4724)

Labelled source text:

> python -m pip show willdisplayinformationaboutaparticularpackage:

Surrounding canonical source context:

> alled requests-2.7.0
> 96 Chapter12. VirtualEnvironmentsandPackages
>
> PythonTutorial,Release3.11.0
> python -m pip uninstall followedbyoneormorepackagenameswillremovethepackagesfromthevirtual
> environment.
> python -m pip show willdisplayinformationaboutaparticularpackage:
> (tutorial-env) $ python -m pip show requests
> ---
> Metadata-Version: 2.0
> Name: requests
> Version: 2.7.0
> Summary: Python HTTP for Humans.
> Home-page: http://python-requests.org
> Author: Kenneth Reitz
> Autho

Fact `pdf-pip-show-list-2`:

python -m pip list displays all packages installed in the environment.

Alternative `pdf-pip-show-list-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5056, 5135)

Labelled source text:

> python -m pip list willdisplayallofthepackagesinstalledinthevirtualenvironment:

Surrounding canonical source context:

> s.
> Home-page: http://python-requests.org
> Author: Kenneth Reitz
> Author-email: me@kennethreitz.com
> License: Apache 2.0
> Location: /Users/akuchling/envs/tutorial-env/lib/python3.4/site-packages
> Requires:
> python -m pip list willdisplayallofthepackagesinstalledinthevirtualenvironment:
> (tutorial-env) $ python -m pip list
> novas (3.1.1.3)
> numpy (1.9.2)
> pip (7.0.3)
> requests (2.7.0)
> setuptools (16.0)
> python -m pip freeze will produce a similar list of the installed packages, but the ou

Review decision / disagreements / resolution: **pending**

## pdf-argparse-help

held_out / pdf-argparse / exact_api / draft

Which help option is available without adding it explicitly in the argparse tutorial?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-argparse-help-1`:

The --help option, also available as -h, is supplied automatically.

Alternative `pdf-argparse-help-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [3413, 3624)

Labelled source text:

> • The --help option, which can also be shortened to-h, is the only option we get for free (i.e. no need to
> specifyit). Specifyinganythingelseresultsinanerror. Buteventhen,wedogetausefulusagemessage,also
> forfree.

Surrounding canonical source context:

> ningthescriptwithoutanyoptionsresultsinnothingdisplayedtostdout. Notsouseful.
> • Thesecondonestartstodisplaytheusefulnessofthe argparsemodule. Wehavedonealmostnothing,but
> alreadywegetanicehelpmessage.
> • The --help option, which can also be shortened to-h, is the only option we get for free (i.e. no need to
> specifyit). Specifyinganythingelseresultsinanerror. Buteventhen,wedogetausefulusagemessage,also
> forfree.
> 3 Introducing Positional arguments
> Anexample:
> import argparse
> parser = argparse.ArgumentParser()
> parser.add_argument("echo")
> args = parser.parse_args()
> print(args.echo)
> Andrunningthecode:
> $ python3 p

Review decision / disagreements / resolution: **pending**

## pdf-argparse-positional

held_out / pdf-argparse / multi_span / draft

What does add_argument specify and what data does parse_args return in the echo example?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-argparse-positional-1`:

add_argument declares the command-line arguments the program accepts.

Alternative `pdf-argparse-positional-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [4093, 4268)

Labelled source text:

> • We’veaddedthe add_argument()method,whichiswhatweusetospecifywhichcommand-lineoptions
> theprogramiswillingtoaccept. Inthiscase,I’venamedit echosothatit’sinlinewithitsfunction.

Surrounding canonical source context:

> ts are required: echo
> $ python3 prog.py --help
> usage: prog.py [-h] echo
> positional arguments:
> echo
> options:
> -h, --help show this help message and exit
> $ python3 prog.py foo
> foo
> Hereiswhat’shappening:
> • We’veaddedthe add_argument()method,whichiswhatweusetospecifywhichcommand-lineoptions
> theprogramiswillingtoaccept. Inthiscase,I’venamedit echosothatit’sinlinewithitsfunction.
> • Callingourprogramnowrequiresustospecifyanoption.
> • The parse_args()methodactuallyreturnssomedatafromtheoptionsspecified,inthiscase, echo.
> • Thevariableissomeformof‘magic’that argparseperformsforfre

Fact `pdf-argparse-positional-2`:

parse_args returns parsed argument values; the example accesses the echo value through args.echo.

Alternative `pdf-argparse-positional-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [4320, 4408)

Labelled source text:

> • The parse_args()methodactuallyreturnssomedatafromtheoptionsspecified,inthiscase, echo.

Surrounding canonical source context:

> t()method,whichiswhatweusetospecifywhichcommand-lineoptions
> theprogramiswillingtoaccept. Inthiscase,I’venamedit echosothatit’sinlinewithitsfunction.
> • Callingourprogramnowrequiresustospecifyanoption.
> • The parse_args()methodactuallyreturnssomedatafromtheoptionsspecified,inthiscase, echo.
> • Thevariableissomeformof‘magic’that argparseperformsforfree(i.e. noneedtospecifywhichvariable
> that value is stored in). You will also notice that its name matches the string argument given to the me

Review decision / disagreements / resolution: **pending**

## pdf-argparse-optional

held_out / pdf-argparse / paraphrase / draft

What value is assigned to the optional verbosity argument if it is omitted?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-argparse-optional-1`:

The omitted optional verbosity argument receives None.

Alternative `pdf-argparse-optional-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [7110, 7365)

Labelled source text:

> • Toshowthattheoptionisactuallyoptional,thereisnoerrorwhenrunningtheprogramwithoutit. Notethat
> bydefault,ifanoptionalargumentisn’tused,therelevantvariable,inthiscase args.verbosity,isgiven
> Noneasavalue,whichisthereasonitfailsthetruthtestofthe ifstatement.

Surrounding canonical source context:

> erbosity VERBOSITY]
> prog.py: error: argument --verbosity: expected one argument
> Hereiswhatishappening:
> • Theprogramiswrittensoastodisplaysomethingwhen --verbosityisspecifiedanddisplaynothingwhen
> not.
> • Toshowthattheoptionisactuallyoptional,thereisnoerrorwhenrunningtheprogramwithoutit. Notethat
> bydefault,ifanoptionalargumentisn’tused,therelevantvariable,inthiscase args.verbosity,isgiven
> Noneasavalue,whichisthereasonitfailsthetruthtestofthe ifstatement.
> • Thehelpmessageisabitdifferent.
> • Whenusingthe --verbosityoption,onemustalsospecifysomevalue,anyvalue.
> Theaboveexampleacceptsarbitraryintegervaluesfor --verbosity,butforoursimpleprogram,onlytwovalue

Review decision / disagreements / resolution: **pending**

## pdf-argparse-store-true

held_out / pdf-argparse / exact_api / draft

What are the verbose variable values when a store_true flag is present or absent?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.
- Included the store_true action identity so the True/False explanation is self-contained.

Fact `pdf-argparse-store-true-1`:

action=store_true sets args.verbose to True when the flag is present and False when absent.

Alternative `pdf-argparse-store-true-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [8325, 8529)

Labelled source text:

> tomatchthatidea. Notethatwenowspecifyanewkeyword, action,andgiveitthevalue "store_true".
> This means that, if the option is specified, assign the valueTrue to args.verbose. Not specifying it
> implies False.

Surrounding canonical source context:

> page)
> -h, --help show this help message and exit
> --verbose increase output verbosity
> Hereiswhatishappening:
> • Theoptionisnowmoreofaflagthansomethingthatrequiresavalue. Weevenchangedthenameoftheoption
> tomatchthatidea. Notethatwenowspecifyanewkeyword, action,andgiveitthevalue "store_true".
> This means that, if the option is specified, assign the valueTrue to args.verbose. Not specifying it
> implies False.
> • Itcomplainswhenyouspecifyavalue,intruespiritofwhatflagsactuallyare.
> • Noticethedifferenthelptext.
> 4.1 Short options
> Ifyouarefamiliarwithcommandlineusage,youwillnoticethatIhaven’tyettouchedonthetopi

Review decision / disagreements / resolution: **pending**

## pdf-argparse-count

held_out / pdf-argparse / multi_span / draft

Why does the count example need default zero after replacing equality tests with greater-than-or-equal tests?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.
- Replaced the unrelated str exponentiation TypeError with the NoneType/integer comparison error, and added the explanation of why default=0 fixes it.
- Removed the incidental count-action definition from the required answer; the question asks about None/default=0, not what count means.

Fact `pdf-argparse-count-2`:

Without the count flag, verbosity is None; comparing it with an integer using >= raises TypeError.

Alternative `pdf-argparse-count-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [13448, 13518)
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [14534, 14605)

Labelled source text:

> • Andifyoudon’tspecifythe -vflag,thatflagisconsideredtohave Nonevalue.

Surrounding canonical source context:

> eviousversionofourscript. That
> shouldexplainthecomplaint.
> 8
>
> • Italsobehavessimilarto“store_true”action.
> • Nowhere’sademonstrationofwhatthe“count”actiongives. You’veprobablyseenthissortofusagebefore.
> • Andifyoudon’tspecifythe -vflag,thatflagisconsideredtohave Nonevalue.
> • Asshouldbeexpected,specifyingthelongformoftheflag,weshouldgetthesameoutput.
> • Sadly,ourhelpoutputisn’tveryinformativeonthenewabilityourscripthasacquired,butthatcanalwaysbe
> fixedbyimprovingthedocume

Labelled source text:

> TypeError: '>=' not supported between instances of 'NoneType' and 'int'

Surrounding canonical source context:

>  -vvv
> the square of 4 equals 16
> $ python3 prog.py 4 -vvvv
> the square of 4 equals 16
> $ python3 prog.py 4
> Traceback (most recent call last):
> File "prog.py", line 11, in <module>
> if args.verbosity >= 2:
> TypeError: '>=' not supported between instances of 'NoneType' and 'int'
> • First output went well, and fixes the bug we had before. That is, we want any value >= 2 to be as verbose as
> possible.
> • Thirdoutputnotsogood.
> Let’sfixthatbug:
> import argparse
> parser = argparse.Arg

Fact `pdf-argparse-count-3`:

Setting default=0 gives an integer even when the flag is absent, so integer verbosity-threshold comparisons work.

Alternative `pdf-argparse-count-3`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [15224, 15475)

Labelled source text:

> We’vejustintroducedyetanotherkeyword, default. We’vesetitto 0inordertomakeitcomparabletotheother
> intvalues. Rememberthatbydefault,ifanoptionalargumentisn’tspecified,itgetsthe Nonevalue,andthatcannot
> becomparedtoanintvalue(hencethe TypeErrorexception).

Surrounding canonical source context:

> rse_args()
> answer = args.square**2
> if args.verbosity >= 2:
> print(f"the square of {args.square} equals {answer}")
> elif args.verbosity >= 1:
> print(f"{args.square}^2 == {answer}")
> else:
> print(answer)
> 9
>
> We’vejustintroducedyetanotherkeyword, default. We’vesetitto 0inordertomakeitcomparabletotheother
> intvalues. Rememberthatbydefault,ifanoptionalargumentisn’tspecified,itgetsthe Nonevalue,andthatcannot
> becomparedtoanintvalue(hencethe TypeErrorexception).
> And:
> $ python3 prog.py 4
> 16
> You can go quite far just with what we’ve learned so far, and we have only scratched the surface. Theargparse
> moduleisverypowerful,andwe’llexploreabitmoreofitbeforeweendth

Review decision / disagreements / resolution: **pending**

## pdf-argparse-exclusive

held_out / pdf-argparse / paraphrase / draft

Why can the tutorial’s verbose and quiet options not be used together?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the question, all reference facts and labelled spans against the full canonical PDF page text and surrounding examples.

Fact `pdf-argparse-exclusive-1`:

The verbose and quiet flags are added to the same mutually exclusive argument group.

Alternative `pdf-argparse-exclusive-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [17733, 17896)

Labelled source text:

> group = parser.add_mutually_exclusive_group()
> group.add_argument("-v", "--verbose", action ="store_true")
> group.add_argument("-q", "--quiet", action ="store_true")

Surrounding canonical source context:

> Let’salsochangetherestoftheprogramsothatthenewfunctionalitymakesmoresense: we’llintroducethe
> --quietoption,whichwillbetheoppositeofthe --verboseone:
> import argparse
> parser = argparse.ArgumentParser()
> group = parser.add_mutually_exclusive_group()
> group.add_argument("-v", "--verbose", action ="store_true")
> group.add_argument("-q", "--quiet", action ="store_true")
> parser.add_argument("x", type=int, help ="the base ")
> parser.add_argument("y", type=int, help ="the exponent ")
> args = parser.parse_args()
> answer = args.x**args.y
> if args.quiet:
> print(answer)
> elif ar

Fact `pdf-argparse-exclusive-2`:

The program allows either flag but forbids specifying both together.

Alternative `pdf-argparse-exclusive-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [19556, 19679)

Labelled source text:

> Notethatslightdifferenceintheusagetext. Notethe [-v | -q] ,whichtellsusthatwecaneitheruse -vor -q,
> butnotbothatthesametime:

Surrounding canonical source context:

> gs = parser.parse_args()
> answer = args.x**args.y
> if args.quiet:
> print(answer)
> elif args.verbose:
> print(f"{args.x} to the power {args.y} equals {answer}")
> else:
> print(f"{args.x}^{args.y} == {answer}")
> Notethatslightdifferenceintheusagetext. Notethe [-v | -q] ,whichtellsusthatwecaneitheruse -vor -q,
> butnotbothatthesametime:
> $ python3 prog.py --help
> usage: prog.py [-h] [-v | -q] x y
> calculate X to the power of Y
> positional arguments:
> x the base
> y the exponent
> options:
> -h, --help show this help message and exit
> -v, --verb

Review decision / disagreements / resolution: **pending**
