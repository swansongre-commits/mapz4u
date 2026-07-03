"""Phase 1 - 인물 수집. 모델 지식 생성(역사·과학·예술 인물, API 불필요).
주제당 1명 = 5명. 반고정관념 최소 2명(메리 애닝-여성 고생물학자, 신사임당·전형필 등).
서사는 시행착오담(성취담 아님), 직업 계보 one-to-many(§4.2).
"""
import sys
sys.path.insert(0, ".")
from common import p, write_json

PEOPLE = [
    dict(id="person-dino", name="메리 애닝", era="1799-1847 영국", topic_tags=["dino"],
         verb_desc="바닷가 절벽에서 화석을 찾아내고, 그 뼈가 무슨 동물인지 탐구했어요",
         story_trial="가난한 집 딸이라 학교도 제대로 못 다녔고, 여자라서 학회에도 못 들어갔어요. "
                     "그래도 위험한 절벽을 오르내리며 처음 보는 화석을 계속 찾아냈고, 여러 번 틀리고 다시 맞춰보며 "
                     "물고기도마뱀(어룡)의 정체를 밝혀냈어요.",
         sites=["dino-04", "dino-06"], job_lineage=["고생물학자", "화석 발굴가", "박물관 큐레이터", "지질학자"],
         anti_stereotype=1),
    dict(id="person-space", name="이원철", era="1896-1963 한국", topic_tags=["space"],
         verb_desc="밤하늘의 별을 관측하고, 우리나라에 천문학을 처음 뿌리내리게 했어요",
         story_trial="유학 시절 낯선 언어로 어려운 천문학을 공부하느라 많이 헤맸어요. "
                     "한국인 최초로 천문학 박사가 되었지만, 관측 장비도 부족한 나라에서 하나하나 만들어가며 "
                     "표준시와 달력을 바로잡는 일을 해냈어요.",
         sites=["space-02", "space-03"], job_lineage=["천문학자", "기상학자", "천문대 연구원", "과학 교육자"],
         anti_stereotype=0),
    dict(id="person-animal", name="제인 구달", era="1934- 영국", topic_tags=["animal"],
         verb_desc="숲속에서 침팬지를 오래 지켜보며 동물의 마음을 이해하려 했어요",
         story_trial="대학도 안 나온 젊은 여성이 아프리카 정글로 혼자 떠난다고 하자 모두가 말렸어요. "
                     "처음엔 침팬지들이 도망가서 몇 달 동안 아무것도 못 봤지만, 포기하지 않고 기다린 끝에 "
                     "침팬지도 도구를 쓴다는 걸 세계 최초로 발견했어요.",
         sites=["animal-01", "animal-02"], job_lineage=["동물행동학자", "사육사", "환경운동가", "생태 다큐 제작자"],
         anti_stereotype=1),
    dict(id="person-robot", name="장영실", era="1390?-1450? 조선", topic_tags=["robot"],
         verb_desc="스스로 움직이는 기계를 만들어 시간과 날씨를 재는 장치를 발명했어요",
         story_trial="노비 신분으로 태어나 관청의 허드렛일을 했지만, 손재주와 궁리하는 힘이 남달랐어요. "
                     "여러 번 실패하고 다시 만들며 스스로 시간을 알리는 물시계 자격루와 비의 양을 재는 측우기를 완성했어요. "
                     "신분의 벽을 기술로 넘어선 사람이에요.",
         sites=["robot-01", "space-01"], job_lineage=["기계공학자", "로봇공학자", "발명가", "제어 기술자"],
         anti_stereotype=1),
    dict(id="person-art", name="신사임당", era="1504-1551 조선", topic_tags=["art"],
         verb_desc="풀과 벌레, 꽃을 자세히 관찰해서 살아있는 듯한 그림으로 표현했어요",
         story_trial="여자는 그림을 배우기 어렵던 시대에, 마당의 풀벌레를 하루하루 관찰하며 스스로 그리는 법을 익혔어요. "
                     "잘 안 그려지면 몇 번이고 다시 그렸고, 작은 풀꽃 하나도 소홀히 하지 않아 조선 최고의 초충도 화가가 되었어요.",
         sites=["art-01", "art-03"], job_lineage=["화가", "일러스트레이터", "식물 세밀화가", "미술 교육자"],
         anti_stereotype=1),
]

def main():
    write_json(p("data", "raw", "people.json"), PEOPLE)
    anti = sum(x["anti_stereotype"] for x in PEOPLE)
    print(f"인물 저장: {len(PEOPLE)}명 → data/raw/people.json (반고정관념 {anti}명)")

if __name__ == "__main__":
    main()
