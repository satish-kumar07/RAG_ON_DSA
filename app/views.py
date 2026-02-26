from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

import requests

def home(request):
    return render(request, "index.html")

def ask(request):
    if request.method == "POST":
        question = request.POST.get("question")

        if not question:
            return JsonResponse({"error": "Missing 'question'"}, status=400)

        try:
            resp = requests.post(
                settings.DSA_BACKEND_START_URL,
                json={"query": question},
                timeout=60,
            )

            if resp.status_code != 200:
                return JsonResponse(
                    {"error": f"Backend error ({resp.status_code}): {resp.text}"},
                    status=502,
                )

            data = resp.json()
            decision = data.get("decision")
            if not decision:
                return JsonResponse(
                    {"error": "Backend response missing 'decision'"},
                    status=502,
                )

            return JsonResponse({"answer": decision, "time": data.get("time")})

        except requests.RequestException as e:
            return JsonResponse({"error": f"Backend unavailable: {str(e)}"}, status=502)

    return JsonResponse({"error": "Method not allowed"}, status=405)