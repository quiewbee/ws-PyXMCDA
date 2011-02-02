import tempfile
import subprocess

def create_input_file(alt_id, crit_id, pt, cat_id, cat_rank, assign, weights=None, lbda=None, profiles=None):
    f = tempfile.NamedTemporaryFile(delete=False)
    if not f:
        return None

    f.write("param ncat := %d;\n" % len(cat_id))
    f.write("param nalt := %d;\n" % len(alt_id))
    f.write("param ncrit := %d;\n" % len(crit_id))
    f.write("param perfs :\t")
    for i in range(len(crit_id)):
        f.write("%d\t" % (i+1))
    f.write(":=\n")
    for i in range(len(alt_id)):
        f.write("\t%d\t" % (i+1))
        perfs = pt[alt_id[i]]
        for j in range(len(crit_id)):
            f.write("%f\t" % perfs[crit_id[j]])
        f.write("\n")
    f.write(";\n")

    f.write("param assign :=")
    for i in range(len(alt_id)):
        f.write("[%d] %d " % ((i+1), cat_rank[assign[alt_id[i]]]))
    f.write(";\n")

    if weights <> None:
        f.write("param weight :=")
        for i in range(len(crit_id)):
            f.write("[%d] %f " % ((i+1), weights[crit_id[j]]))
        f.write(";\n")
        f.write("param weight := %f;\n" % lbda)

    f.write("end;\n")
    f.flush()

    return f

def solve(model_file, input_file):
    p = subprocess.Popen(["glpsol", "-m", "%s" % model_file, "-d", "%s" % input_file], stdout=subprocess.PIPE)

    output = p.communicate()
    status = p.returncode

    return (status, output[0])

def parse_output(output, alt_id, crit_id):
    found = output.rfind("INTEGER OPTIMAL SOLUTION FOUND")
    if found < 0:
        print "Integer optimal solution not found"
        return

    glpk_weigths = (output.partition("\n### Criteria weights ###\n")[2]).partition("\n### Criteria weights ###\n")[0]
    w = glpk_weigths.split()
    weights = {}
    for i, crit in enumerate(crit_id):
        weights[crit] = w[i]
        
    glpk_profiles = (output.partition("\n### Profiles ###\n")[2]).partition("\n### Profiles ###\n")[0]
    profiles = []
    for profile in glpk_profiles.split("\n"):
        prof = profile.split()
        refs = {}
        q = {}
        p = {}
        for i, crit in enumerate(crit_id):
            refs[crit] = prof[i]
            q[crit] = 0
            p[crit] = 0
        profiles.append({'refs': refs, 'p': p, 'q': q, 'v': {}})

    glpk_lambda = (output.partition("### Lambda ###\n")[2]).partition("### Lambda ###\n")[0]
    lbda = glpk_lambda

    glpk_compat = (output.partition("### Compatible alternatives ###\n")[2]).partition("### Compatible alternatives ###\n")[0]
    compatibility = glpk_compat.split()
    compat = {}
    for i, alt in enumerate(alt_id):
        compat[alt] = compatibility[i]

    return (weights, profiles, lbda, compat)
