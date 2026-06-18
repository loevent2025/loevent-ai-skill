# Web3 · Developer Meetup · Venue Selection Criteria Knowledge Base

## Scale Quick Reference

| Scale Level | Headcount | Typical Scenarios |
|-------------|-----------|-------------------|
| Small Technical Salon | 15–40 | Closed-door protocol discussion, contract audit sharing, core contributor gathering |
| Standard Meetup | 40–80 | Technical talks + protocol demo + community networking |
| Large Meetup | 80–150 | Ecosystem joint event, L1 developer day, conference side event |
| Hack Night | 30–100 | Contract development, protocol integration, on-chain tooling hands-on |

---

# Selection Criteria

---

## Criterion 1: Technical Infrastructure Reliability (Hard Requirement)

**Definition:**
Whether the venue has stable infrastructure to support technical presentations and live on-chain demos. The unique risk with Web3 demos is that on-chain interactions, node connections, and wallet signing are extremely sensitive to network stability and access permissions—firewalled networks or excessive latency will directly cause demo failures.

**Evaluation Areas:**

Network
- Upload + download bandwidth ≥ 100 Mbps (200 Mbps recommended for 80+ attendees)
- Wi-Fi supporting high-concurrency connections (estimate 80% of attendees online simultaneously)
- Wired network access available in the presentation area (on-chain demos should prioritize wired connections)
- No port restrictions, no firewall blocking (must be able to access: major RPC nodes, Infura/Alchemy/QuickNode, IPFS, blockchain explorers for all major chains)
- Whether personal routers or standalone hotspot connections are permitted
- Backup network plan available (4G/5G mobile hotspots)

⚠️ Web3-Specific Risk: Some corporate/tech park networks block access to overseas nodes. RPC connectivity must be tested on-site in advance—verbal assurances are not acceptable.

Presentation Equipment
- HDMI / USB-C ports available with common adapters on standby
- Projector or screen resolution ≥ 1080p (contract code and transaction hashes must be clearly legible)
- Stable microphones with no feedback (wireless preferred)
- Audio system supports video playback

Power
- Independent power outlets in the presentation area and demo zone
- Each audience row accessible to power (developers are sensitive to laptop battery levels)
- Total load capacity supports 10+ devices running simultaneously

---

## Criterion 2: Spatial Structure & Interaction Adaptability (Hard Requirement)

**Definition:**
A Web3 Meetup operates in two states: technical presentations (focused, quiet, sightlines converging) and community networking (fluid, free-form, multi-point conversations).

**Evaluation Areas:**

Presentation Mode
- Unobstructed sightlines from the presentation area; 100% of seats can see the screen
- Movable or flexibly rearrangeable seating
- Audience members can easily stand to ask questions during Q&A
- Clear visual focal point separating the presentation area from the audience

Networking Mode
- Ample standing and mingling space (the Web3 community prefers walk-around networking)
- Natural gathering points: tea break station, high-top tables, corridor areas
- Dedicated demo corner (allowing multiple people to gather around on-chain interactions)
- Ceiling height ≥ 3 m (to avoid a cramped feel)
- Overall spatial atmosphere encourages peer-to-peer exchange rather than a "speaker talks, audience listens" dynamic

⚠️ Benchmark: After the event ends, would attendees have both the reason and the space to spontaneously cluster in corners to continue discussing protocol details?

---

## Criterion 3: Web3 Industry Alignment (High-Weight Criterion)

**Definition:**
Whether the spatial character matches Web3 developer culture. The Web3 community's core cultural values are decentralization, open-source ethos, and geek libertarianism—with strong aversion to anything "overly commercialized," "too corporate," or "performative," alongside a natural affinity for "authenticity," "grassroots energy," and "hack culture."

**Web3 Positioning:**
> Geeky, but not messy
> Community-driven, but not amateurish
> Free-spirited, but not disorganized

**✅ Suitable Space Types:**
- Converted creative park spaces (industrial style, warehouse conversions, lofts)
- Co-working spaces (open layout, without excessive corporate décor)
- Blockchain/Web3 company office spaces
- University tech club venues (aligned with open-source culture)
- Basements or semi-underground spaces (if well-equipped, these are actually a bonus in the Web3 context)

**❌ Space Types to Avoid:**
- Traditional hotel ballrooms (excessively corporate feel, strongly conflicts with Web3 culture)
- Overly polished corporate meeting rooms ("office meeting vibe" undermines community atmosphere)
- Luxury venues (the Web3 community has an instinctive aversion to opulence—easily triggers "where did this money come from?" skepticism)
- Heavily branded sponsor venues (the community will perceive it as "being marketed to")

---

## Criterion 4: On-Chain Demo & Protocol Showcase Support (High-Weight Criterion)

**Definition:**
The core demo scenarios at Web3 Meetups are fundamentally different from AI events: on-chain interactions, contract deployment, wallet connections, and real-time node responses are the primary showcase content, requiring exceptionally high network access freedom and stability.

**Evaluation Areas:**

General Demo Support
- Dedicated demo corner capable of running 2–5 stations simultaneously
- Independent power per station (not sharing the same outlet)
- Real-time audio/video playback support
- On-site screen recording and livestreaming permitted
- Moderate lighting (dim environments are acceptable in Web3 settings, but screens must remain clearly visible)

Web3-Specific Requirements
- Unrestricted network access to: major public chain RPC nodes (Ethereum, Solana, BNB Chain, etc.), blockchain explorers (Etherscan, etc.), IPFS nodes
- Stable network latency (on-chain transaction broadcasting and confirmation demos are latency-sensitive)
- Support for MetaMask/hardware wallet local signing demos (no cloud dependency required)
- Screen mirroring supports simultaneous multi-window display (contract code, transaction records, frontend interface side by side)
- Presenters permitted to connect their own nodes or local testnets

---

## Criterion 5: Capacity & Comfortable Density Management (Hard Requirement)

**Definition:**
The venue maintains a "lively but manageable" state at the target headcount. Web3 Meetups tolerate slightly higher density—"huddling together to discuss" is inherently aligned with hack culture—but it must not impair device operation or basic comfort.

**Area Reference Standards:**

| Mode | Area per Person |
|------|-----------------|
| Theater-style presentations | 1–1.2 m² |
| Standing social networking | 1.5 m² |
| Hack Night | 2 m² |

**Evaluation Areas:**
- Base calculations on comfortable capacity, not the venue's stated maximum occupancy
- Whether HVAC and ventilation are independently controllable (high-density crowds + multiple devices generating heat make climate control critical)
- HVAC response speed in summer/winter conditions
- Restroom count (recommend 1 per 50 attendees)
- If outdoor or semi-outdoor areas exist, whether a viable rain contingency plan is available

---

## Criterion 6: Time Flexibility & Usage Elasticity (Hard Requirement)

**Definition:**
Web3 developers are distributed across time zones (often needing to accommodate overseas community schedules), discussions tend to run long, and Hack Nights may extend through the night. Time flexibility is generally more important in Web3 scenarios than in AI Commercial scenarios.

**Evaluation Areas:**
- Standard time slot supported: 6:00 PM–10:00 PM
- Overtime usage permitted (with reasonable billing terms)
- No restrictions on nighttime entry/exit (security/access control cooperation)
- Latest teardown time clearly defined (can the venue support until 11:00 PM or later)
- Early access permitted 2–3 hours in advance for setup
- Free-form networking permitted to continue after the official program ends

Hack Night Scenario: Time flexibility escalates to the primary hard requirement. Confirm whether overnight use is supported, and whether security and HVAC remain operational throughout.

---

## Criterion 7: Transportation & Accessibility (Flexible Criterion)

**Definition:**
The Web3 developer community has a slightly higher tolerance for "traveling a bit farther for a great event" compared to AI Commercial audiences, but transportation accessibility still affects attendance rates, especially among non-core community members.

**Evaluation Areas:**
- Within a 15-minute walk from a metro station (Web3 can tolerate up to 15 minutes; AI Commercial recommends 10 minutes)
- Ride-hailing accessible (with a clearly defined pickup/drop-off point)
- Safe late-night departure (surrounding environment, lighting conditions)
- Clear venue entrance signage, easy to navigate (especially important for non-standard venues)
- Permission to place event wayfinding signage

⚠️ Core Web3 community members have higher acceptance of "remote but interesting venues." Venue character can compensate for transportation drawbacks, but detailed navigation instructions must be included in event communications.

---

## Criterion 8: Community Building Potential (Flexible Criterion)

**Definition:**
Whether the venue supports long-term Web3 community building and organic growth. Unlike AI Commercial events, the Web3 community places less emphasis on "brand authority" and more on a sense of belonging—"this place is our home base."

**Evaluation Areas:**
- Whether long-term or recurring use is permitted (building "regular community hub" recognition)
- Whether photo-friendly areas exist (for social media distribution, with an authentic rather than polished aesthetic)
- Full-event photography and publishing permitted
- Support for community retention actions (group chat QR codes, wallet address scanning, etc.)
- Whether the venue operator is a Web3 industry participant or community-friendly (ecosystem synergy as a bonus)
- Whether the community is allowed to bring in its own decorations or modifications (enhancing the sense of belonging)

⚠️ Key Difference from AI Commercial: AI Commercial emphasizes branded backdrops and visual presentation; the Web3 community may react negatively to large branded backdrops, perceiving them as "being co-opted by sponsors." Brand presence should be more restrained and community-native.

---

## Criterion 9: Operational Compliance & Usage Restrictions (Flexible Criterion)

**Definition:**
Whether the venue has usage restrictions that could impact normal event operations. Web3 events use non-standard venues (lofts, warehouses, basements) more frequently than AI Commercial events, requiring thorough verification of usage restrictions.

**Evaluation Areas:**
- Whether maximum occupancy is clearly defined
- Whether public technical events are permitted (some office buildings have restrictions)
- Whether commercial event restrictions or additional approvals apply
- Whether outside food and beverages are permitted on-site
- Usage compliance for non-standard venues (whether the lease agreement permits this type of event)
- Whether venue liability insurance coverage is clearly defined

---

# Default Priority Ranking

## Hard Requirements (Disqualify Immediately if Unmet)
1. Technical Infrastructure Reliability (especially: overseas node access permissions)
2. Spatial Structure & Interaction Adaptability
3. Capacity & Comfortable Density
4. Time Flexibility & Usage Elasticity

## High-Weight Criteria (Strongly Influence Decision)
5. Web3 Industry Alignment
6. On-Chain Demo & Protocol Showcase Support

## Flexible Criteria (Evaluate Based on Specific Circumstances)
7. Transportation & Accessibility
8. Community Building Potential
9. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Handling Guidelines

### Technical Talks + Reception
- Prioritize evaluating "theater → social" turnover time (whether ≤ 30 minutes)
- Whether lighting supports brightness adjustment (Web3 events prefer dimmer ambient lighting; avoid fluorescent lights)
- Whether fixed furniture can be quickly removed or folded

### Meetup + Hack Night
- Network bandwidth standard elevated to 200 Mbps
- Overseas node access permissions escalate to the first verification item
- Power requirements: independent outlet per workstation
- Time flexibility escalates to the primary hard requirement (confirm overnight feasibility)
- Area calculated at 2 m² per person

### Meetup + Side Event (Conference Peripheral Event)
- Prioritize venues within walking distance of the main conference venue (attendees are reluctant to travel long distances between events)
- Brand presence should be restrained (avoid over-commercialization that could damage community perception)
- Strict timing required (attendees have packed schedules during conference periods; teardown times must be precise)
- Network independence is especially important (networks near conference venues are typically congested)