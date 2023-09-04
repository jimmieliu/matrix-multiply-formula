def brace_formula(fstr):
    if "+" in fstr and "(" != fstr[0] and ")" != fstr[1]:
        return f"({fstr})"
    return fstr


class Matrix:
    def __init__(self, prefix="q", size=(3, 3), mat=None):
        if mat is not None:
            self.mat = mat
            self.size = (len(mat), len(mat[0]))
            return
        assert len(size) == 2
        res = []
        for i in range(size[0]):
            row = []
            for j in range(size[1]):
                row.append(f"{prefix}{i}{j}")
            res.append(row)
        self.mat = res
        self.size = size

    def __str__(self) -> str:
        r = []
        for row in self.mat:
            r.append(f"| {' '.join(row)} |")
        return "\n".join(r) + "\n"

    @property
    def T(self):
        res = []
        for j in range(self.size[1]):
            row = []
            for i in range(self.size[0]):
                row.append(self.mat[i][j])
            res.append(row)
        return Matrix(mat=res)

    def mm(self, m2):
        res = []
        for i in range(self.size[0]):
            row = []
            for j in range(m2.size[1]):
                _sum = []
                for k in range(m2.size[0]):
                    _sum.append(
                        f"{brace_formula(self.mat[i][k])}{brace_formula(m2.mat[k][j])}"
                    )
                row.append("+".join(_sum))
            res.append(row)
        return Matrix(mat=res)

    def sum(self, axis):
        res = []
        if axis == 0:
            row = []
            for j in range(self.size[1]):
                _sum = []
                for i in range(self.size[0]):
                    _sum.append(self.mat[i][j])
                row.append("+".join(_sum))
            res.append(row)
        elif axis == 1:
            for i in range(self.size[0]):
                row = []
                _sum = []
                for j in range(self.size[1]):
                    _sum.append(self.mat[i][j])
                row.append("+".join(_sum))
                res.append(row)
        else:
            raise NotImplementedError

        return Matrix(mat=res)

    def __getitem__(self, index):
        return self.mat[index]

    def element_wise(self, m2, sign):
        res = []
        m2 = Broadcast2Matrix(m2, self.size)

        brace = brace_formula if sign in ["/", "*"] else (lambda x: x)
        for i in range(self.size[0]):
            row = []
            for j in range(self.size[1]):
                row.append(f"{brace(self.mat[i][j])}{sign}{brace(m2[i][j])}")
            res.append(row)
        return Matrix(mat=res)
    
    def element_wise_div(self, m2):
        return self.element_wise(m2, "/")


class Broadcast2Matrix:
    def __init__(self, mat, size) -> None:
        if isinstance(mat, str):
            self.get_item = lambda i: mat
            return

        if isinstance(mat, list):
            assert isinstance(mat[0], str)
            self.get_item = lambda i: mat[0]
            return

        assert isinstance(mat, Matrix)
        assert len(size) == len(mat.size)

        if mat.size[0] == 1:
            self.get_item = lambda i: mat[0]
        elif mat.size[1] == 1:

            def _get_item(i):
                return Broadcast2Matrix(mat[i], (mat.size[1],))

            self.get_item = _get_item
        else:
            self.get_item = mat.__getitem__

    def __getitem__(self, index):
        return self.get_item(index)


def expand_multiply_brace(formu):
    def _expand(_formu):
        # if depth <= 0:
        #     return formu
        bst = _formu.index("(")
        assert bst > 0
        assert _formu[-1] == ")"
        res = []
        ele = _formu[:bst]
        if ele[-1] in ("/", "-", "+"):
            return _formu
        st = bst + 1
        bunfinish = 0
        for i in range(bst + 1, len(_formu) - 2):
            c = _formu[i]
            if c == "(":
                bunfinish += 1
            elif c == ")":
                bunfinish -= 1
            elif bunfinish == 0 and (c == "+" or c == "-"):
                res += f"{ele}{_formu[st:i]}{c}"
                st = i + 1

        res.append(f"{ele}{_formu[st:len(_formu)-1]}")

        return "".join(res)

    res = []
    st = 0
    bunfinish = 0
    for i in range(len(formu)):
        c = formu[i]
        if c == "(":
            bunfinish += 1
        elif c == ")":
            bunfinish -= 1
        elif bunfinish == 0 and (c == "+" or c == "-"):
            end = i
            res.append(_expand(formu[st:end]))
            res.append(c)
            st = i + 1

        if i == len(formu) - 1:
            assert bunfinish == 0
            end = i + 1
            res.append(_expand(formu[st:end]))

    return "".join(res)


def split_denominater(formu):
    bunfinish = 0
    for i in range(len(formu)):
        c = formu[i]
        if c == "(":
            bunfinish += 1
        elif c == ")":
            bunfinish -= 1
        elif bunfinish == 0 and c == "/":
            return formu[:i], formu[i + 1 :]
        elif bunfinish == 0 and (i == len(formu) - 1):
            return formu[:i], ""


def assemble_frac(num_list, denom):
    if denom != "":
        denom = f"/{denom}"
    if len(num_list) > 1:
        return f"({''.join(num_list)}){denom}"
    return f"{''.join(num_list)}{denom}"


def merge_same_denominator(formu):
    denominaters = {}
    first_denom = None

    def _add(_formu, _last_sign, _first_denom):
        num, denom = split_denominater(_formu)
        if _first_denom is None:
            _first_denom = denom
        if denom not in denominaters:
            denominaters[denom] = []
        denominaters[denom].append(f"{_last_sign}{num}")
        return _first_denom

    last_sign = ""
    st = 0
    bunfinish = 0
    for i in range(len(formu)):
        c = formu[i]
        if c == "(":
            bunfinish += 1
        elif c == ")":
            bunfinish -= 1
        elif bunfinish == 0 and (c == "+" or c == "-"):
            end = i
            first_denom = _add(formu[st:end], last_sign, first_denom)
            last_sign = c
            st = i + 1

        if i == len(formu) - 1:
            assert bunfinish == 0
            end = i + 1
            first_denom = _add(formu[st:end], last_sign, first_denom)

    res = []
    v = denominaters.pop(first_denom)
    res.append(f"{assemble_frac(v, first_denom)}")

    for k, v in denominaters.items():
        if v[0][0] == "+":
            sign = "+"
        elif v[0][0] == "-":
            sign = "-"
        else:
            raise NotImplementedError

        v[0] = v[0][1:]

        if sign == "-":
            for i in range(1, len(v)):
                if v[i][0] == "+":
                    v[i][0] = "-"
                elif v[i][0] == "-":
                    v[i][0] = "+"
                else:
                    raise NotImplementedError

        res.append(f"{sign}{assemble_frac(v, k)}")
    return "".join(res)

def get_I_hat():
    q = Matrix("q", (2, 2))
    print(q)

    k = Matrix("k", (2, 2))
    print(k)

    # print(q.sum(0))
    # print(q.sum(1))
    O = k.mm(q.sum(0).T)
    # I = q.mm(k.sum(0).T)

    kj_div_Oj = k.element_wise_div(O)
    print(kj_div_Oj)
    kj_div_Oj_sum = kj_div_Oj.sum(0)
    print(kj_div_Oj_sum)
    res = q.mm(kj_div_Oj_sum.T)
    print(res)

    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = expand_multiply_brace(res.mat[i][j])

    print(res)

    res = res.sum(0)
    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = merge_same_denominator(res.mat[i][j])
    print(res)

def get_O_hat():
    q = Matrix("q", (2, 2))
    print(q)

    k = Matrix("k", (2, 2))
    print(k)

    # print(q.sum(0))
    # print(q.sum(1))
    # O = k.mm(q.sum(0).T)
    I = q.mm(k.sum(0).T)

    qj_div_Ij = q.element_wise_div(I)
    print(qj_div_Ij)
    qj_div_Ij_sum = qj_div_Ij.sum(0)
    print(qj_div_Ij_sum)
    res = k.mm(qj_div_Ij_sum.T)
    print(res)

    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = expand_multiply_brace(res.mat[i][j])

    print(res)

    res = res.sum(0)
    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = merge_same_denominator(res.mat[i][j])
    print(res)


def get_biased_I():
    q = Matrix("q", (2, 2))
    k = Matrix("k", (2, 2))
    b = Matrix("b", (2, 2))
    I = q.mm(k.sum(0).T)
    bsum = b.sum(1)
    print(I.size)
    print(bsum.size)

    I_biased = I.element_wise(bsum, "+")
    print(I_biased)

def get_biased_O():
    q = Matrix("q", (2, 2))
    k = Matrix("k", (2, 2))
    b = Matrix("b", (2, 2))
    O = k.mm(q.sum(0).T)
    bsum = b.sum(0).T
    print(O.size)
    print(bsum.size)

    O_biased = O.element_wise(bsum, "+")
    print(O_biased)

def get_biased_I_hat():
    q = Matrix("q", (2, 2))
    k = Matrix("k", (2, 2))
    b = Matrix("b", (2, 2))
    # I = q.mm(k.sum(0).T)
    # bsum = b.sum(1)
    # print(I.size)
    # print(bsum.size)

    # I_biased = I.element_wise(bsum, "+")
    # print(I_biased)
    O = k.mm(q.sum(0).T)
    bsum = b.sum(0).T
    O = O.element_wise(bsum, "+")
    
    kj_div_Oj = k.element_wise_div(O)
    # print(kj_div_Oj)
    kj_div_Oj_sum = kj_div_Oj.sum(0)
    # print(kj_div_Oj_sum)
    res = q.mm(kj_div_Oj_sum.T)

    # b.sum(1) # [Li, 1]
    # O # [Lj, 1]

    I_hat_b = b.element_wise_div(O.T).sum(1)
    print("THIS\n", I_hat_b)
    res = res.element_wise(I_hat_b, "+")

    # print(q)

    # print(kj_div_Oj_sum.T)


    print(res)

    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = expand_multiply_brace(res.mat[i][j])

    print(res)

    res = res.sum(0)
    for i in range(res.size[0]):
        for j in range(res.size[1]):
            res.mat[i][j] = merge_same_denominator(res.mat[i][j])
    print(res)

if __name__ == "__main__":
    # get_I_hat()
    # get_O_hat()
    # b = Matrix("b", (2, 2))
    # get_biased_I()
    # get_biased_O()

    get_biased_I_hat()
