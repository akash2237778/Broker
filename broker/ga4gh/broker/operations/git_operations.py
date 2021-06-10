from ga4gh.broker.operations.container_build import createImage
from git import Repo
import subprocess as sb


def gitCheckout(url: str, branch: str, commit: str):
    repo = Repo.clone_from(url, "clone_dir")
    repo.heads.branch.checkout()
    past_branch = repo.create_head('broker', commit)
    repo.head.reference = past_branch
    repo.head.reset(index=True, working_tree=True)
    createImage("path" , "tag", "dockerfile")
    return "Successfully cloned and checkout!"
    


#sb.getoutput("rm -rf clone")

    # repo = Repo.clone_from("https://github.com/akash2237778/CI-CD", "clone")
    # repo.heads.branch.checkout()
    # past_branch = repo.create_head('broker', 'e07d03b')
    # repo.head.reference = past_branch
    # repo.head.reset(index=True, working_tree=True)