# Web3 · Technical Workshop · Venue Selection Criteria Knowledge Base

## Scale Quick Reference

| Scale Level | Headcount | Typical Scenarios |
|-------------|-----------|-------------------|
| Boutique Small Class | 10–25 | Smart contract audit training, core protocol contributor workshop, closed-door developer seminar |
| Standard Workshop | 25–50 | Solidity/Rust introduction, DeFi protocol integration, wallet development training |
| Large Workshop | 50–100 | L1 ecosystem developer education, community technical training, conference-affiliated workshop |
| Extra-Large Workshop | 100+ | Multi-track parallel developer training, ecosystem course series |

---

## Layout Type Reference

| Layout Type | Use Case | Headcount | Core Venue Requirements |
|-------------|----------|-----------|------------------------|
| Island Cluster | Protocol collaborative development, group hands-on | 20–60 | ≥ 2.5 m² per person, aisle width ≥ 1.2 m |
| U-Shape | Small class interaction, contract audit seminar | 15–30 | Ample space for instructor movement, full sightline alignment |
| Classroom (Row Seating) | Coding hands-on, high content-density technical training | 25–80 | Desktop width ≥ 80 cm per person, independent power per table |
| Theater + Hands-On Split | Large workshops with separate lecture and hands-on zones | 80–150 | Two independent areas with segmented network and power |

---

## Functional Zone Reference

| Functional Zone | Area Share | Core Configuration Requirements |
|-----------------|------------|--------------------------------|
| Teaching / Hands-On Area | 60–70% | Full coverage of desks, power, and network; unobstructed sightlines |
| Instructor Area | 10–15% | Podium or workstation, main screen, space for roaming guidance |
| Tea Break / Rest Area | 10–15% | Dedicated zone with community free-exchange character; not shared with hands-on area |
| Q&A / Mentoring Area | 5–10% | Semi-isolated corner supporting 1-on-1 contract code review or debugging mentorship |

---

# Selection Criteria

---

## Criterion 1: Network & Technical Infrastructure (Primary Hard Requirement)

**Definition:**
Network risk at Web3 Technical Workshops differs from AI Commercial Workshops: bandwidth is typically not the bottleneck—the core threat is blockchain node access being blocked by firewalls. During hands-on segments, all participants need simultaneous access to testnet RPC nodes, contract deployment, and on-chain contract interactions. If nodes become inaccessible, the entire class's hands-on progress halts simultaneously, with no way to "switch to a different exercise" as a workaround.

**Evaluation Areas:**

Network Bandwidth & Concurrency
- Total bandwidth ≥ 200 Mbps (500 Mbps recommended for 50+ participants)
- Support for all participants (100% online rate) simultaneously accessing on-chain nodes and RPC services
- Wired + wireless dual coverage (wired preferred in hands-on areas)
- Wired access points: 1 wired connection per 2–4 participants
- Venue-wide Wi-Fi coverage with no dead zones; AP count matched to participant density

Access Permissions (Core Web3 Requirement)
- No port restrictions, no firewall blocking
- Unrestricted access to major testnet RPC nodes: Ethereum Sepolia/Goerli, Solana Devnet, BNB Testnet, Polygon Mumbai, etc.
- Unrestricted access to node service providers: Infura, Alchemy, QuickNode, Ankr
- Unrestricted access to blockchain explorers: Etherscan, Solscan, etc. (for contract verification and transaction lookups)
- Unrestricted access to development dependencies: GitHub, npm, crates.io (for Rust/Solana development), Foundry/Hardhat dependency sources
- Personal routers or standalone hotspot connections permitted (strongly recommended as a standard backup)

Backup Plans
- 4G/5G hotspots available as emergency backup
- Whether the venue permits pre-deploying local nodes (Ganache/Anvil/Hardhat Network local chain as a fallback when RPC nodes are inaccessible)

Power (Hard Requirement on Par with Network)
- At least 1 outlet per 2 participants (participants typically carry laptop + phone)
- Power strips or desk-embedded outlets configured per table
- Independent power circuit for the instructor area
- Total circuit load supports all participant devices running simultaneously


## Criterion 2: Teaching Space Quality & Hands-On Adaptability (Hard Requirement)

**Definition:**
Web3 Workshops are typically 4–8 hours of long-duration, high-density hands-on work, with contract development, protocol debugging, and on-chain interactions demanding intense focus. Space quality directly impacts participant engagement and learning outcomes—though the Web3 community cares far less about whether a space is "polished enough" than whether it is "functional enough."

**Evaluation Areas:**

Desktops & Seating
- Desktop width ≥ 80 cm per person (must accommodate laptop, notebook, beverage simultaneously)
- Desktop depth ≥ 60 cm (space for external keyboard/mouse use)
- Chairs suitable for extended use (with backrest; not folding chairs)
- Shoulder-to-shoulder spacing between adjacent participants ≥ 60 cm (no interference during hands-on work)

Sightlines & Instructor Area
- All seats have unobstructed view of the main screen
- Distance from the last row to the main screen does not exceed 6× the screen width (contract code must be clearly legible)
- Instructor area has ample roaming space (contract review and debugging mentorship require walking to individual participants)
- Instructor can conveniently reach any participant's position

Environmental Quality
- Independently controllable HVAC (high stability required for extended full-capacity use)
- Adjustable lighting (terminals and code editors suffer from screen glare in high-brightness environments)
- No strong light sources creating direct glare on screens
- Relatively quiet with effective isolation from external noise

## Criterion 3: Instructor Demonstration & Teaching Equipment Support (Hard Requirement)

**Definition:**
Instructor demonstrations at Web3 Workshops are extremely technically dense: Solidity/Rust contract code, terminal commands, real-time blockchain explorer data, wallet interaction interfaces. Screen resolution requirements are equivalent to AI Commercial Workshops, but the content type means whiteboards are used more frequently (architecture diagrams, state variable explanations, call stack walkthroughs).

**Evaluation Areas:**

Screen & Projection
- Main screen/projector resolution ≥ 1080p (contract code and terminal output must be clearly legible)
- Screen size matched to the farthest seat distance (recommended: minimum 12pt font legible from the last row)
- Dual-screen output support (instructor preview screen + participant main screen)
- Multi-source signal switching support (instructor laptop + blockchain explorer auxiliary screen)
- HDMI / USB-C ports available with adapters on standby

Audio & Microphones
- Audio coverage across the full venue (microphone is a must for 30+ participants)
- At least 1 wireless microphone (needed when the instructor roams for guidance)
- No feedback risk

Whiteboard & Auxiliary Tools
- Whiteboard or writable display surface available (architecture diagrams and call flow diagrams are used at extremely high frequency in Web3 Workshops)
- Whiteboard size matched to the space; legible from all participant seats
- Adequate supply of whiteboard markers and erasers

Recording Conditions (If Recording Is Required)
- Venue permits full-session recording (the Web3 community is highly dependent on course recording distribution for secondary reach)
- Suitable camera mounting positions available (main screen + instructor view)

---

## Criterion 4: Web3 Industry Alignment (High-Weight Criterion)

**Definition:**
Web3 Workshop audiences are core members of the developer community—contract engineers, protocol developers, full-stack Web3 developers. This group judges a space by whether it feels like "our people's place," whether it's geeky enough, and whether it embodies the open-source spirit—with clear aversion to excessive formality, a "training center" feel, or corporate atmosphere. This is the most fundamental alignment difference from AI Commercial Workshops.

**Web3 Workshop Positioning:**
> Geeky enough for developers to feel this is "where our kind gathers"
> Open enough for peer-to-peer technical exchange to happen naturally
> Functional is sufficient—no bonus points needed for décor that doesn't improve learning outcomes

**✅ Suitable Space Types:**
- Dedicated training areas in co-working spaces (strong sense of openness, no corporate formality)
- Blockchain/Web3 company office spaces (strong ecosystem affinity, developers feel a sense of belonging)
- Converted creative park spaces or lofts (industrial style, free-spirited atmosphere aligned with hack culture)
- University computer science or engineering classrooms (high open-source culture alignment, de-commercialized)
- University or community hackerspaces

**❌ Space Types to Avoid:**
- Traditional hotel meeting rooms (excessive business and consumer atmosphere, strongly conflicts with Web3 developer culture)
- Standardized corporate training centers ("employee training vibe" undermines the community's culture of peer-level equality)
- Excessively decorated commercial venues (the Web3 community has an instinctive aversion to formalism and opulence)
- Purely consumer-oriented venues (mall event spaces, influencer-style cafés)


## Criterion 5: Capacity & Comfortable Density Management (Hard Requirement)

**Definition:**
Web3 Workshops involve long-duration, high-density hands-on work with per-person space requirements equivalent to AI Commercial Workshops. Web3 developers have low tolerance for "not enough functional space" but high tolerance for "not polished enough"—function over form.

**Area Reference Standards:**

| Layout Type | Area per Person |
|-------------|-----------------|
| Classroom Row Seating | 1.5–2 m² |
| Island Cluster | 2–2.5 m² |
| U-Shape | 2.5–3 m² |

**Evaluation Areas:**
- Base calculations on comfortable capacity, not the venue's stated maximum occupancy
- Independently controllable HVAC (high stability required for extended full-capacity use)
- Adjustable lighting (terminals and code editors suffer from glare in high-brightness environments)
- Restroom count (recommend 1 per 50 participants)
- Tea break area is dedicated and not shared with the hands-on area

---

## Criterion 6: Time Flexibility & Usage Elasticity (Hard Requirement)

**Definition:**
Web3 Workshops have higher time uncertainty than AI Commercial equivalents: contract debugging overruns, on-chain interaction confirmation wait times, unpredictable depth of participant questions—technical discussions in the Web3 community have a natural tendency to extend.

**Evaluation Areas:**
- Full-day use supported (9:00 AM–6:00 PM) or half-day use (flexible segments)
- Overtime usage permitted (with reasonable billing terms)
- Early access permitted 1–2 hours in advance for setup and network testing (RPC node testing takes time)
- Free-form networking permitted to continue after the program ends (informal discussions in the Web3 community carry extremely high value and should not be cut short by immediate venue clearance)
- Latest teardown time clearly defined

Multi-Day Workshop Scenario: Confirm the feasibility of consecutive-day bookings at the same venue, as well as guaranteed daily early-access setup time.

---

## Criterion 7: Transportation & Accessibility (High-Weight Criterion)

**Definition:**
Web3 developers have higher tolerance for "traveling farther for a great event" than general audiences, but transportation accessibility for full-day weekday workshops still affects punctuality—late arrivals disrupt the instructor's pace and the continuity of participants' hands-on progress.

**Evaluation Areas:**
- Within a 15-minute walk from a metro station (Web3 can tolerate up to 15 minutes)
- Ride-hailing accessible (with a clearly defined pickup/drop-off point)
- Safe late-night departure (post-workshop extended socializing often runs into the evening)
- Clear venue entrance signage (non-standard venues require advance navigation planning)
- Permission to place event wayfinding signage

## Criterion 8: Community Building & Long-Term Reuse Potential (Flexible Criterion)

**Definition:**
Web3 Workshops have far lower branding requirements than AI Commercial events, placing greater value on the sense of belonging to "the community's own learning hub." For course series, a fixed venue builds community memory—which is more valuable than visual brand presentation.

**Evaluation Areas:**
- Whether long-term or recurring use is permitted (establishing a fixed community learning hub for course series)
- Whether the venue operator is a Web3 ecosystem participant (ecosystem affinity as a bonus)
- Full-session recording and publishing permitted (the Web3 community depends on course recording distribution)
- Support for community retention actions (group chat QR codes, community scanning)
- Availability of areas suitable for informal gathering (technical discussions during breaks and after sessions are equally valuable)
- Whether the community is allowed to bring in its own decorations or modifications (enhancing the sense of belonging)

## Criterion 9: Operational Compliance & Usage Restrictions (Flexible Criterion)

**Definition:**
Web3 Workshops use non-standard venues at a higher rate than AI Commercial events, requiring item-by-item verification of usage restrictions. Additionally, some venues have specific restrictions on blockchain and cryptocurrency-related training activities that must be confirmed in advance.

**Evaluation Areas:**
- Whether maximum occupancy is clearly defined and meets requirements
- Whether paid training events are permitted (some office buildings or parks have restrictions)
- Whether there are specific restrictions on blockchain/cryptocurrency-themed events (some government/state-owned enterprise venues have these)
- Whether outside food is permitted on-site (lunch arrangements for full-day workshops)
- Whether noise restrictions apply (hands-on discussion and debugging segments generate a certain noise level)
- Whether venue liability insurance coverage is clearly defined

---

# Default Priority Ranking

## Hard Requirements (Disqualify Immediately if Unmet)
1. Network & Technical Infrastructure (especially: overseas RPC node access permissions, testnet connectivity)
2. Teaching Space Quality & Hands-On Adaptability (desktop space, sightlines, environment)
3. Instructor Demonstration & Teaching Equipment Support (screen clarity, whiteboard)
4. Capacity & Comfortable Density Management
5. Time Flexibility & Usage Elasticity

## High-Weight Criteria (Strongly Influence Decision)
6. Web3 Industry Alignment
7. Transportation & Accessibility

## Flexible Criteria (Evaluate Based on Specific Circumstances)
8. Community Building & Long-Term Reuse Potential
9. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Handling Guidelines

### Workshop + Meetup (Morning Workshop + Afternoon Meetup)
- Space must support rapid layout transitions (classroom → open flow, turnover time ≤ 1 hour)
- Network bandwidth set to the higher standard across both scenarios; RPC access permissions maintained throughout
- Instructor demo equipment shared with Meetup presentation equipment; compatibility must be confirmed in advance
- Time flexibility must satisfy both scenarios simultaneously; afternoon Meetup start time needs a buffer

### Workshop + Hackathon (Training Day + Development Day)
- Network bandwidth standard elevated to hackathon level (≥ 500 Mbps)
- RPC node access verification scope expanded to mainnet (hackathon phase may require mainnet demonstrations)
- Power density upgraded (independent outlet per workstation during hackathon phase)
- Time flexibility escalates to the primary hard requirement (hackathon development phase may extend into late night or overnight)
- Area calculated at hackathon standard (≥ 2 m² per person)

### Multi-Track Parallel Workshops (Multiple Concurrent Training Rooms)
- Independent network circuit per room (to prevent RPC node access bandwidth competition)
- Independent HVAC control per room
- Acoustic isolation between rooms required (contract debugging and Q&A sessions generate a certain noise level)
- Shared tea break area sized based on total headcount (the tea break area in multi-track workshops is also the core node for cross-track community exchange)

### Boutique Small Class Workshop (10–25 Participants)
- Layout preference for U-shape or island cluster (aligned with Web3's peer-to-peer collaboration culture)
- Web3 company meeting rooms or private co-working rooms are viable options (at small scale, alignment matters more than comprehensive facilities)
- Instructor demo equipment requirements remain unchanged (screen clarity is non-negotiable)
- RPC node access verification is equally critical—requirements are not relaxed due to smaller scale