"""Site-wide template context for author and social links."""


def author_info(request):
    return {
        "AUTHOR": {
            "name": "JARPULANIRJALA",
            "phone": "+91 7842849340",
            "email": "nirjala8462@gmail.com",
            "linkedin": "https://www.linkedin.com/in/nirjala-jarpula-749346321/",
            "github": "https://github.com/Jarpula-Nirjala/HybridDualNetPath",
            "gfg": "https://auth.geeksforgeeks.org/user/nirjala8462/",
            "leetcode": "https://leetcode.com/u/nirjala8462/",
            "college": "Indian Institute of Information Technology, Surat",
            "degree": "B.Tech Electronics & Communication Engineering",
            "years": "2022 – 2026",
            "cgpa": "7.14",
        }
    }
