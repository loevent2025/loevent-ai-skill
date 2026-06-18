# AI Commercial · Technical Workshop · Venue Selection Criteria Knowledge Base

## Capacity Quick Reference

| Scale | Headcount | Typical Scenario |
|-------|-----------|-----------------|
| Boutique Small Class | 10–25 | AI Agent architecture seminars, enterprise private deployment training, invitation-only product-technical alignment workshops |
| Standard Workshop | 25–50 | LLM application development basics, AI Agent integration hands-on, RAG system building training |
| Large Workshop | 50–100 | Enterprise AI transformation developer education, vertical industry technical training, conference-affiliated workshops |
| Extra-Large Workshop | 100+ | Multi-track parallel AI skills training, ecosystem course series, company-wide AI enablement |

---

## Layout Type Reference

AI Commercial Workshop layout preferences lean toward professionalism and efficiency. Classroom-style seating is widely accepted in enterprise and commercial settings because it aligns with expectations for "serious technical training." Island-style layouts suit collaborative hands-on work, while U-shape layouts are ideal for highly interactive small-class seminars.

| Layout Type | Use Case | Headcount | Core Venue Requirements |
|-------------|----------|-----------|------------------------|
| Classroom (Rows) | Coding hands-on, API integration, content-dense technical training | 25–80 | Desk width ≥80cm/person, independent power per table |
| Grouped Islands | Agent collaborative development, team exercises, Prompt engineering | 20–60 | ≥2.5 m²/person, aisle width ≥1.2m |
| U-Shape | Small-class interaction, product-technical alignment, solution seminars | 15–30 | Ample space for instructor movement, unobstructed sightlines for all attendees |
| Theater + Hands-On Split | Large workshops with separate lecture and hands-on zones | 80–150 | Two independent areas with separate network and power |

---

## Functional Zone Reference

| Zone | Area Share | Core Configuration Requirements |
|------|-----------|-------------------------------|
| Teaching / Hands-On Area | 60–70% | Full coverage of desks, power, and network; unobstructed sightlines |
| Instructor Area | 10–15% | Podium or workstation, main display, space for roaming guidance |
| Refreshment / Break Area | 10–15% | Separate zone with a relaxed social atmosphere; must not overlap with hands-on area |
| Q&A / Mentoring Area | 5–10% | Semi-isolated corner supporting 1-on-1 code reviews or model debugging sessions |

---

# Selection Criteria

---

## Criterion 1: Network & Technical Infrastructure (Top Hard Requirement)

**Definition:**
During hands-on sessions, all participants need to simultaneously call AI model APIs, access cloud inference services, and download model dependencies. If API endpoints become unreachable or bandwidth is severely insufficient, every participant's hands-on progress halts at once — and there is no way to work around it by "switching to a different exercise."

**Evaluation Checklist:**

Network Bandwidth & Concurrency
- Total bandwidth ≥200 Mbps (≥500 Mbps recommended for 50+ attendees)
- Support 100% simultaneous online rate for all attendees calling cloud AI inference APIs (high-density concurrent requests)
- Dual wired + wireless coverage (wired priority for hands-on areas)
- Wired access points: 1 Ethernet port per 2–4 attendees
- Zero-dead-zone WiFi coverage with AP density matched to attendee density

Access Permissions (Core AI Commercial Requirement)
- No port restrictions, no firewall blocking
- Unrestricted access to mainstream AI model APIs: OpenAI API, Anthropic Claude API, Google Gemini API, Azure OpenAI Service, Tongyi Qianwen API, Wenxin Yiyan API, etc.
- Unrestricted access to AI development platforms: HuggingFace, Replicate, Together AI, Groq, etc.
- Unrestricted access to vector database services: Pinecone, Weaviate, Chroma, Qdrant, etc. (essential for RAG hands-on exercises)
- Unrestricted access to development dependencies: GitHub, PyPI (pip), npm, Conda/Mamba repositories
- Unrestricted access to cloud service consoles: AWS, GCP, Azure, Alibaba Cloud (confirm based on course content)
- Permission to connect external routers or independent hotspots (strongly recommended as a standard backup)

Backup Plans
- 4G/5G hotspots provisioned as emergency fallback
- Whether the venue permits pre-deployment of local inference services (Ollama / vLLM / LocalAI as a fallback when API access is disrupted)
- Whether the instructor's machine can run local demo models (to avoid single-point dependency on commercial APIs)

Power (Hard Requirement on Par with Network)
- At least 1 outlet per 2 attendees (participants typically carry a laptop + phone; some bring external GPUs or drives)
- Power strips or built-in desk outlets at every table
- Independent power circuit for the instructor area
- Total circuit load supports all devices running simultaneously

---

## Criterion 2: Teaching Space Quality & Hands-On Suitability (Hard Requirement)

**Definition:**
AI Commercial Workshops typically run 4–8 hours of intensive hands-on work. Code debugging, Prompt engineering, Agent orchestration, and API integration demand extreme focus. Space quality directly impacts attendee performance and learning outcomes. AI Commercial audiences have specific expectations around whether a space "feels professional enough" — functionality and professionalism carry equal weight.

**Evaluation Checklist:**

Desks & Seating
- Desk width ≥80cm/person (must accommodate laptop, notebook, and drink simultaneously)
- Desk depth ≥60cm (space for external keyboard/mouse use)
- Chairs suitable for extended sitting (with backrests, not folding chairs)
- Shoulder-to-shoulder spacing between adjacent attendees ≥60cm (no interference during hands-on work)

Sightlines & Instructor Area
- All seats have an unobstructed view of the main screen
- Distance from the last row to the main screen does not exceed 6× the screen width (code and Prompt content must be clearly readable)
- Instructor area has ample roaming space (code reviews and debugging guidance require walking to individual attendees)
- Instructor can conveniently reach any attendee's seat

Environmental Quality
- Independently controllable air conditioning (high occupancy over extended hours demands stable temperature control)
- Adjustable lighting (terminal and code editor screens suffer glare under harsh lighting)
- No strong reflective light sources hitting screens directly
- Relatively quiet with effective isolation from external noise

---

## Criterion 3: Instructor Demonstration & Teaching Equipment (Hard Requirement)

**Definition:**
AI Commercial Workshop instructor demos are technically dense: Python code, API call logs, model output comparisons, Agent execution chains, terminal commands, and cloud platform consoles. These require extremely high screen resolution and font readability. Whiteboard usage is also frequent (system architecture diagrams, Agent call chains, RAG pipeline diagrams).

**Evaluation Checklist:**

Screens & Projection
- Main screen/projector resolution ≥1080p (code, terminal output, and API responses must be clearly readable)
- Screen size matched to the farthest seat distance (recommended: 12pt font legible from the back row)
- Dual-screen output support (instructor preview screen + attendee main screen)
- Multi-source switching support (instructor laptop + auxiliary demo screen)
- Full HDMI / USB-C port availability with backup adapters

Audio & Microphones
- Sound system covers the entire room (microphone is mandatory for 30+ attendees)
- At least 1 wireless microphone (required when the instructor roams for guidance)
- No feedback/howling risk

Whiteboard & Auxiliary Tools
- Whiteboard or writable display surface available (extremely frequent use for AI system architecture diagrams, Agent call chains, and RAG pipeline walkthroughs)
- Whiteboard size matched to the space; legible from all seats
- Adequate supply of whiteboard markers and erasers

Recording Conditions (If Recording Is Required)
- Venue permits full-session recording (workshop recordings have high value for internal enterprise distribution and follow-up learning)
- Suitable positions for mounting camera equipment (capturing both the main screen and instructor)

---

## Criterion 4: AI Commercial Industry Aesthetic Alignment (High-Weight Criterion)

**Definition:**
AI Commercial Workshop attendees are enterprise technical teams, AI application developers, and product/engineering leaders. This audience judges venues on a clear set of criteria: Is it professional enough? Does it convey a sense of efficiency? Does it match the atmosphere of "serious work?" They have a notable aversion to overly casual, disorganized, or informal-feeling venues. This is the most fundamental aesthetic difference compared to Web3 Workshops.

**AI Commercial Workshop Aesthetic Positioning:**
> Clean and professional — participants should feel they are attending "serious technical training"
> Efficiency-oriented — supports a high-density learning pace
> Aligned with the rigor of commercial implementation — no need for hacker aesthetics or counterculture vibes

**✅ Suitable Space Types:**
- Professional training centers or enterprise training rooms (strong sense of professionalism, well-equipped, matches commercial training expectations)
- Corporate conference centers or private co-working meeting rooms (efficiency-focused, aligned with AI commercial application contexts)
- Hotel meeting rooms (professional atmosphere with comprehensive support services; suitable for out-of-town attendees)
- Tech park or startup incubator training spaces (tech-forward feel aligned with the AI industry aesthetic)
- University computer science or business school classrooms (strong learning atmosphere, minimal entertainment distractions)

**❌ Space Types to Avoid:**
- Trendy cafés or entertainment-oriented commercial venues (casual atmosphere disrupts intensive learning flow)
- Noisy open-plan co-working halls (noise and distractions undermine focus)
- Excessively industrial or stark loft spaces (visual disconnect from the professionalism expected in commercial AI)
- Legacy venues with outdated facilities and weak network infrastructure (substandard technical infrastructure directly derails hands-on sessions)

---

## Criterion 5: Capacity & Comfortable Density Control (Hard Requirement)

**Definition:**
AI Commercial Workshops involve extended, intensive hands-on work, with per-person space requirements comparable to Web3 Workshops. AI Commercial participants have specific expectations around spatial professionalism; overcrowding directly impacts experience ratings.

**Space Standards by Layout:**

| Layout Type | Area per Person |
|-------------|----------------|
| Classroom Rows | 1.5–2 m² |
| Grouped Islands | 2–2.5 m² |
| U-Shape | 2.5–3 m² |

**Evaluation Checklist:**
- Use comfortable capacity as the benchmark, not the venue's stated maximum occupancy
- Independently controllable air conditioning (high occupancy over extended hours demands stable temperature)
- Adjustable lighting (code editors and terminals suffer glare under harsh lighting)
- Restroom count (recommended: 1 per 50 attendees)
- Refreshment area is separate and does not overlap with the hands-on area

---

## Criterion 6: Time Flexibility & Usage Elasticity (Hard Requirement)

**Definition:**
AI Commercial Workshops carry inherent time uncertainty: API debugging overruns, model output reviews, and unpredictable depth of attendee questions — especially in enterprise contexts, where discussions about specific business problems naturally expand beyond schedule.

**Evaluation Checklist:**
- Supports full-day use (9:00–18:00) or half-day use (flexible blocks)
- Allows overtime use (with reasonable billing terms)
- Allows 1–2 hours early access for setup and technical debugging (API connectivity testing and environment configuration verification require time)
- Permits informal networking to continue after the event ends (post-workshop discussions on AI commercialization carry high value)
- Clearly defined latest vacate time

For multi-day workshops: confirm that consecutive bookings at the same venue are feasible, and that daily early-access setup time is guaranteed.

---

## Criterion 7: Transportation & Accessibility (High-Weight Criterion)

**Definition:**
AI Commercial Workshop participants are predominantly working professionals. For full-day weekday workshops, transportation convenience directly impacts punctuality — late arrivals disrupt the instructor's pace and break the continuity of hands-on exercises. Enterprise clients have lower tolerance for inconvenient access compared to Web3 developer communities.

**Evaluation Checklist:**
- Within a 10-minute walk from a metro station (AI Commercial audiences have high expectations for transit convenience)
- Adequate nearby parking (some participants drive)
- Rideshare-friendly (clear pickup/drop-off points)
- Clear venue entrance signage and accurate navigation
- Safe nighttime departure (extended networking may continue into the evening)
- Permission to place event wayfinding signage

---

## Criterion 8: Brand Presence & Commercial Display Capability (High-Weight Criterion)

**Definition:**
AI Commercial Workshops have higher brand presentation requirements than Web3 Workshops. Brand visibility for enterprise organizers, partners, and sponsors is a legitimate need for commercial events and also serves as a signal of event professionalism to attendees. This is one of the most notable differences from Web3 Workshops.

**Evaluation Checklist:**
- Permission to place branded backdrops, pop-up banner stands, and tabletop materials
- Suitable blank walls or display areas for brand presentation
- Whether the venue accepts co-branded event signage (co-hosting arrangements)
- Support for check-in desk and wayfinding desk setup
- Permission for full-session recording and publication (workshop recordings serve brand promotion and attendee retention)
- Support for community engagement actions (QR code scanning for group chats, social media follows, etc.)

---

## Criterion 9: Operational Compliance & Usage Restrictions (Negotiable Criterion)

**Definition:**
AI Commercial Workshops are typically held at standardized commercial venues where usage restrictions are relatively clear-cut, but each item still requires confirmation. Some venues impose additional restrictions on recording and distribution for AI/data-related training — these must be verified in advance.

**Evaluation Checklist:**
- Is the maximum occupancy clearly stated and sufficient for the event?
- Does the venue permit paid training events? (some office buildings or parks have restrictions)
- Is outside catering allowed? (lunch logistics for all-day workshops)
- Are there noise restrictions? (hands-on discussions and debugging sessions generate a certain level of noise)
- Is full-session recording and online distribution permitted? (confirm copyright and privacy-related terms)
- Is venue liability insurance clearly assigned?
- Data security requirements (some enterprise venues have compliance requirements for network access logs)

---

# Default Priority Ranking

## Hard Requirements (Disqualify If Not Met)
1. Network & Technical Infrastructure (especially: overseas AI API access permissions, bandwidth concurrency support)
2. Teaching Space Quality & Hands-On Suitability (desk space, sightlines, environment)
3. Instructor Demonstration & Teaching Equipment (screen clarity, whiteboard)
4. Capacity & Comfortable Density Control
5. Time Flexibility & Usage Elasticity

## High-Weight Criteria (Strongly Influence Decision)
6. AI Commercial Industry Aesthetic Alignment
7. Transportation & Accessibility
8. Brand Presence & Commercial Display Capability

## Negotiable Criteria (Assess Based on Specific Circumstances)
9. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Guidelines

### Workshop + Demo Day (Morning Workshop + Afternoon Demo Showcase)
- Space must support rapid layout transitions (classroom rows → showcase flow; changeover time ≤1 hour)
- Network bandwidth should meet the higher requirement of both scenarios; API access permissions must remain active throughout
- Instructor demo equipment and demo showcase equipment are shared — confirm compatibility in advance
- Time flexibility must satisfy both scenarios; buffer time is needed before the afternoon demo begins
- Brand collateral placement must support the visual needs of both scenarios

### Workshop + Hackathon (Training Day + Build Day)
- Network bandwidth standard elevated to hackathon level (≥500 Mbps)
- API access permission verification scope expanded (hackathon phase may call additional external services)
- Power density upgraded (independent outlet per workstation during hackathon; some participants bring external GPUs)
- Time flexibility elevated to the top hard requirement (hackathon development may extend into late night or overnight)
- Space calculated at hackathon standards (≥2 m²/person)
- Local inference service deployment conditions must be confirmed in advance (hackathon phase demands greater API cost control)

### Multi-Track Parallel Workshops (Concurrent Training Rooms)
- Each room requires an independent network circuit (to prevent AI API call bandwidth from competing across tracks)
- Each room requires independent climate control
- Acoustic isolation between rooms is necessary (debugging and Q&A sessions generate moderate noise)
- Shared refreshment area sized for total headcount (the break area in multi-track workshops also serves as the primary hub for cross-track technical exchange)
- Unified check-in area and brand display zone sized for total headcount

### Boutique Small-Class Workshop (10–25 People)
- Layout preference: U-shape or island-style (suited for small-class interaction and product-technical alignment)
- Consider premium co-working private meeting rooms or executive meeting spaces (at small scale, professionalism and comfort are equally important)
- Instructor demo equipment requirements remain unchanged (screen clarity is paramount)
- AI API access permission verification is equally critical — do not lower standards because of smaller scale
- Brand presence can be more refined and understated, emphasizing quality over scale