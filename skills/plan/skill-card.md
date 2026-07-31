## Description: <br>
Plans tasks before execution by deciding when to plan versus act directly, sizing plan depth to risk, and structuring steps, estimates, rollbacks, checkpoints, and replanning. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[ivangdavila](https://clawhub.ai/user/ivangdavila) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and agent users use this skill to decide when task planning is needed and to produce appropriately scoped plans for multi-step, ambiguous, high-risk, long-running, or irreversible work. It supports planning before execution, human approval checkpoints, estimate ranges, rollback thinking, replanning after deviations, and durable plan records when needed. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill may leave durable planning preferences, active plans, and outcome logs on the local machine. <br>
Mitigation: Review the files under ~/Clawic/data/plan/ and remove records that should not remain on the machine. <br>
Risk: Plans for irreversible or externally visible actions can still be wrong if the user skips review or approval checkpoints. <br>
Mitigation: Use the skill's approval and rollback checkpoints for high-risk steps, especially before deployments, migrations, deletions, or sending anything external. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/ivangdavila/skills/plan) <br>
- [Clawic Plan skill page](https://clawic.com/skills/plan) <br>
- [approval.md](artifact/approval.md) <br>
- [decomposition.md](artifact/decomposition.md) <br>
- [estimation.md](artifact/estimation.md) <br>
- [long-horizon.md](artifact/long-horizon.md) <br>
- [outcomes.md](artifact/outcomes.md) <br>
- [replanning.md](artifact/replanning.md) <br>
- [risk.md](artifact/risk.md) <br>
- [setup.md](artifact/setup.md) <br>
- [strategies.md](artifact/strategies.md) <br>


## Skill Output: <br>
**Output Type(s):** [Guidance, Markdown, Configuration, Files] <br>
**Output Format:** [Markdown planning guidance with optional local configuration and plan record files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May persist planning preferences, active plans, and outcome logs under ~/Clawic/data/plan/ when the workflow calls for durable records.] <br>

## Skill Version(s): <br>
1.0.3 (source: frontmatter and server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
