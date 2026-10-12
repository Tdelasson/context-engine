# English technical-workbench annotation review

Dataset SHA-256: `ce89682465a2e3ac69c7563be7d9dc7288872b7b5b843b38b3677df13fd9fc61`

All annotations are authored drafts. An independent reviewer must check the question, answerability, required facts, each complete alternative, source revision and offsets, category and grouping. Check surrounding source context, not just the excerpt. Record disagreements and resolve them before approval. Do not infer correctness from a successful loader check or approve unseen questions.

To approve reviewed labels, set each dataset query review.status to approved and review.reviewer to your identity. Keep the author identity. Add review notes for disputed or revised labels. Update the dataset version when facts/splits change; rerun recorded comparisons against the new manifest hash. No runner auto-approves annotations.

## pdf-venv-isolation

development / pdf-venv / paraphrase / draft

How do the tutorial virtual environments resolve applications requiring conflicting package versions?

Expected answerable: True

Fact `pdf-venv-isolation-1`:

Different applications can then use different virtual environments. To resolve the earlier example of conflicting re-
quirements, application A can have its own virtual environment with version 1.0 installed while application B has
anothervirtualenvironmentwithversion2.0. IfapplicationBrequiresalibrarybeupgradedtoversion3.0,thiswill
notaffectapplicationA’senvironment.

Alternative `pdf-venv-isolation-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [819, 1189)

Review decision / disagreements / resolution: **pending**

## pdf-venv-module

development / pdf-venv / exact_api / draft

Which Python module creates virtual environments, and which Python installation does it usually use?

Expected answerable: True

Fact `pdf-venv-module-1`:

Themoduleusedtocreateandmanagevirtualenvironmentsiscalled venv. venvwillusuallyinstallthemostrecent
versionofPythonthatyouhaveavailable. IfyouhavemultipleversionsofPythononyoursystem, youcanselecta
specificPythonversionbyrunning python3orwhicheverversionyouwant.

Alternative `pdf-venv-module-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [1223, 1485)

Review decision / disagreements / resolution: **pending**

## pdf-venv-activation

development / pdf-venv / paraphrase / draft

What does activating a virtual environment change about the shell and the python command?

Expected answerable: True

Fact `pdf-venv-activation-1`:

Activating the virtual environment will change your shell’s prompt to show what virtual environment you’re using,
andmodifytheenvironmentsothatrunning pythonwillgetyouthatparticularversionandinstallationofPython.

Alternative `pdf-venv-activation-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [2456, 2668)

Review decision / disagreements / resolution: **pending**

## pdf-pip-version

development / pdf-venv / multi_span / draft

How does pip select an exact package version and upgrade it to the latest version in the tutorial?

Expected answerable: True

Fact `pdf-pip-version-1`:

You can also install a specific version of a package by giving the package name followed by== and the version
number:

Alternative `pdf-pip-version-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [3656, 3773)

Fact `pdf-pip-version-2`:

Ifyoure-runthiscommand, pipwillnoticethattherequestedversionisalreadyinstalledanddonothing. Youcan
supplyadifferentversionnumbertogetthatversion,oryoucanrun python -m pip install --upgrade
toupgradethepackagetothelatestversion:

Alternative `pdf-pip-version-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [3983, 4210)

Review decision / disagreements / resolution: **pending**

## pdf-pip-freeze

development / pdf-venv / multi_span / draft

How does pip freeze format its package list, and how is that requirements file installed?

Expected answerable: True

Fact `pdf-pip-freeze-1`:

python -m pip freeze will produce a similar list of the installed packages, but the output uses the format
that python -m pip install expects. Acommonconventionistoputthislistina requirements.txt
file:

Alternative `pdf-pip-freeze-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5249, 5450)

Fact `pdf-pip-freeze-2`:

The requirements.txtcanthenbecommittedtoversioncontrolandshippedaspartofanapplication. Users
cantheninstallallthenecessarypackageswith install -r :

Alternative `pdf-pip-freeze-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5590, 5737)

Review decision / disagreements / resolution: **pending**

## pdf-pip-show-list

development / pdf-venv / exact_api / draft

Which pip commands show one package’s information and all installed packages?

Expected answerable: True

Fact `pdf-pip-show-list-1`:

python -m pip show willdisplayinformationaboutaparticularpackage:

Alternative `pdf-pip-show-list-1`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [4659, 4724)

Fact `pdf-pip-show-list-2`:

python -m pip list willdisplayallofthepackagesinstalledinthevirtualenvironment:

Alternative `pdf-pip-show-list-2`:
- `python311:pdf:tutorial` revision `bb4acc124833bd5470b2f507097e1774f7260d2f75e5f332b52c212a905c6557` extracted-text characters [5056, 5135)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-help

held_out / pdf-argparse / exact_api / draft

Which help option is available without adding it explicitly in the argparse tutorial?

Expected answerable: True

Fact `pdf-argparse-help-1`:

• The --help option, which can also be shortened to-h, is the only option we get for free (i.e. no need to
specifyit). Specifyinganythingelseresultsinanerror. Buteventhen,wedogetausefulusagemessage,also
forfree.

Alternative `pdf-argparse-help-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [3413, 3624)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-positional

held_out / pdf-argparse / multi_span / draft

What does add_argument specify and what data does parse_args return in the echo example?

Expected answerable: True

Fact `pdf-argparse-positional-1`:

• We’veaddedthe add_argument()method,whichiswhatweusetospecifywhichcommand-lineoptions
theprogramiswillingtoaccept. Inthiscase,I’venamedit echosothatit’sinlinewithitsfunction.

Alternative `pdf-argparse-positional-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [4093, 4268)

Fact `pdf-argparse-positional-2`:

• The parse_args()methodactuallyreturnssomedatafromtheoptionsspecified,inthiscase, echo.

Alternative `pdf-argparse-positional-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [4320, 4408)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-optional

held_out / pdf-argparse / paraphrase / draft

What value is assigned to the optional verbosity argument if it is omitted?

Expected answerable: True

Fact `pdf-argparse-optional-1`:

• Toshowthattheoptionisactuallyoptional,thereisnoerrorwhenrunningtheprogramwithoutit. Notethat
bydefault,ifanoptionalargumentisn’tused,therelevantvariable,inthiscase args.verbosity,isgiven
Noneasavalue,whichisthereasonitfailsthetruthtestofthe ifstatement.

Alternative `pdf-argparse-optional-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [7110, 7365)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-store-true

held_out / pdf-argparse / exact_api / draft

What are the verbose variable values when a store_true flag is present or absent?

Expected answerable: True

Fact `pdf-argparse-store-true-1`:

This means that, if the option is specified, assign the valueTrue to args.verbose. Not specifying it
implies False.

Alternative `pdf-argparse-store-true-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [8414, 8529)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-count

held_out / pdf-argparse / multi_span / draft

Why does the count example need default zero after replacing equality tests with greater-than-or-equal tests?

Expected answerable: True

Fact `pdf-argparse-count-1`:

Wehaveintroducedanotheraction,“count”,tocountthenumberofoccurrencesofspecificoptions.

Alternative `pdf-argparse-count-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [12584, 12669)

Fact `pdf-argparse-count-2`:

TypeError: unsupported operand type(s) for ** or pow(): 'str' and 'int'

Alternative `pdf-argparse-count-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [5628, 5699)

Fact `pdf-argparse-count-3`:

action ="count", default =0,
help="increase output verbosity ")

Alternative `pdf-argparse-count-3`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [14944, 15007)

Review decision / disagreements / resolution: **pending**

## pdf-argparse-exclusive

held_out / pdf-argparse / paraphrase / draft

Why can the tutorial’s verbose and quiet options not be used together?

Expected answerable: True

Fact `pdf-argparse-exclusive-1`:

group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action ="store_true")
group.add_argument("-q", "--quiet", action ="store_true")

Alternative `pdf-argparse-exclusive-1`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [17733, 17896)

Fact `pdf-argparse-exclusive-2`:

Notethatslightdifferenceintheusagetext. Notethe [-v | -q] ,whichtellsusthatwecaneitheruse -vor -q,
butnotbothatthesametime:

Alternative `pdf-argparse-exclusive-2`:
- `python311:pdf:howto-argparse` revision `efe920f4b9f535c3c5be7bd936b72dcff25cf03effad196567c76b3990453455` extracted-text characters [19556, 19679)

Review decision / disagreements / resolution: **pending**
